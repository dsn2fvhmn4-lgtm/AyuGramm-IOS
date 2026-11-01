package main

import (
	"bufio"
	"crypto/sha1"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// A minimal RFC 6455 server: text frames only, which is all the hot reload protocol needs.
// No third-party dependency, so `go build` works offline.

const websocketGUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

type client struct {
	conn   net.Conn
	reader *bufio.Reader
	mutex  sync.Mutex
}

func (c *client) send(text []byte) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	header := []byte{0x81}
	switch length := len(text); {
	case length < 126:
		header = append(header, byte(length))
	case length <= 0xffff:
		header = append(header, 126, byte(length>>8), byte(length))
	default:
		header = append(header, 127)
		var size [8]byte
		binary.BigEndian.PutUint64(size[:], uint64(length))
		header = append(header, size[:]...)
	}
	c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
	if _, err := c.conn.Write(header); err != nil {
		return err
	}
	_, err := c.conn.Write(text)
	return err
}

// read returns the next text message; control frames are answered or end the connection.
func (c *client) read() ([]byte, error) {
	for {
		var head [2]byte
		if _, err := io.ReadFull(c.reader, head[:]); err != nil {
			return nil, err
		}
		opcode := head[0] & 0x0f
		masked := head[1]&0x80 != 0
		length := uint64(head[1] & 0x7f)
		switch length {
		case 126:
			var size [2]byte
			if _, err := io.ReadFull(c.reader, size[:]); err != nil {
				return nil, err
			}
			length = uint64(binary.BigEndian.Uint16(size[:]))
		case 127:
			var size [8]byte
			if _, err := io.ReadFull(c.reader, size[:]); err != nil {
				return nil, err
			}
			length = binary.BigEndian.Uint64(size[:])
		}
		if length > 4<<20 {
			return nil, errors.New("frame too large")
		}
		var mask [4]byte
		if masked {
			if _, err := io.ReadFull(c.reader, mask[:]); err != nil {
				return nil, err
			}
		}
		payload := make([]byte, length)
		if _, err := io.ReadFull(c.reader, payload); err != nil {
			return nil, err
		}
		if masked {
			for i := range payload {
				payload[i] ^= mask[i%4]
			}
		}
		switch opcode {
		case 0x1, 0x2:
			return payload, nil
		case 0x8:
			return nil, io.EOF
		case 0x9:
			c.mutex.Lock()
			c.conn.Write(append([]byte{0x8a, byte(len(payload))}, payload...))
			c.mutex.Unlock()
		}
	}
}

func upgrade(w http.ResponseWriter, r *http.Request) (*client, error) {
	key := r.Header.Get("Sec-WebSocket-Key")
	if key == "" {
		return nil, errors.New("not a WebSocket request")
	}
	hijacker, ok := w.(http.Hijacker)
	if !ok {
		return nil, errors.New("hijacking unsupported")
	}
	conn, buffer, err := hijacker.Hijack()
	if err != nil {
		return nil, err
	}
	sum := sha1.Sum([]byte(key + websocketGUID))
	accept := base64.StdEncoding.EncodeToString(sum[:])
	response := "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + accept + "\r\n\r\n"
	if _, err := conn.Write([]byte(response)); err != nil {
		conn.Close()
		return nil, err
	}
	return &client{conn: conn, reader: buffer.Reader}, nil
}

func pluginMessage(path string) ([]byte, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return json.Marshal(map[string]string{
		"type":     "plugin",
		"filename": filepath.Base(path),
		"source":   base64.StdEncoding.EncodeToString(data),
	})
}

func serveDev(path string, port int) error {
	if _, err := os.Stat(path); err != nil {
		return err
	}
	var mutex sync.Mutex
	clients := map[*client]bool{}
	broadcast := func() {
		message, err := pluginMessage(path)
		if err != nil {
			fmt.Println("read failed:", err)
			return
		}
		mutex.Lock()
		defer mutex.Unlock()
		for c := range clients {
			if err := c.send(message); err != nil {
				c.conn.Close()
				delete(clients, c)
			}
		}
		fmt.Printf("%s  sent %s to %d device(s)\n", time.Now().Format("15:04:05"), filepath.Base(path), len(clients))
	}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		c, err := upgrade(w, r)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		mutex.Lock()
		clients[c] = true
		mutex.Unlock()
		fmt.Println("device connected:", c.conn.RemoteAddr())
		if message, err := pluginMessage(path); err == nil {
			c.send(message)
		}
		go func() {
			defer func() {
				mutex.Lock()
				delete(clients, c)
				mutex.Unlock()
				c.conn.Close()
				fmt.Println("device disconnected:", c.conn.RemoteAddr())
			}()
			for {
				payload, err := c.read()
				if err != nil {
					return
				}
				var event map[string]any
				if json.Unmarshal(payload, &event) == nil {
					switch event["type"] {
					case "installed":
						fmt.Printf("%s  installed %v (%v)\n", time.Now().Format("15:04:05"), event["name"], event["id"])
					case "error":
						fmt.Printf("%s  install error: %v\n", time.Now().Format("15:04:05"), event["message"])
					case "log":
						fmt.Printf("%s  [%v] %v\n", time.Now().Format("15:04:05"), event["level"], event["text"])
					}
				}
			}
		}()
	})

	// Poll the file: no platform-specific watcher, and a save is picked up within 300 ms.
	go func() {
		var last time.Time
		if info, err := os.Stat(path); err == nil {
			last = info.ModTime()
		}
		for range time.Tick(300 * time.Millisecond) {
			info, err := os.Stat(path)
			if err != nil || !info.ModTime().After(last) {
				continue
			}
			last = info.ModTime()
			broadcast()
		}
	}()

	fmt.Printf("ayu dev: serving %s on ws://0.0.0.0:%d\nIn AyuGram: Tools → Hot reload computer → this computer's IP, then turn Hot reload on.\n", path, port)
	return http.ListenAndServe(fmt.Sprintf(":%d", port), nil)
}
