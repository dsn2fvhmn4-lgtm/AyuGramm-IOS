// Package ayu is the AyuGram plugin SDK for TinyGo.
//
// Build:  tinygo build -o plugin.wasm -target wasm-unknown -opt z -no-debug ./
// Then:   ayu pack plugin.wasm manifest.json plugin.wasm
//
// Same ABI as the Rust and Zig SDKs: one import (ayu.host) and four exports
// (ayu_init, ayu_dispatch, ayu_alloc, ayu_free). Requests and answers are JSON.
//
//	package main
//
//	import (
//		"strings"
//		"github.com/murk-sus/ayugram-sdk/ayu"
//	)
//
//	//export ayu_init
//	func ayuInit() {
//		ayu.Before(ayu.OutgoingText, func(text string, ctx ayu.Context) *string {
//			upper := strings.ToUpper(text)
//			return &upper
//		})
//		ayu.Log("loaded")
//	}
//
//	func main() {}
package ayu

import (
	"encoding/json"
	"strconv"
	"unsafe"
)

//go:wasmimport ayu host
func host(pointer unsafe.Pointer, length uint32) uint64

// Hook points.
const (
	OutgoingText  = "message.outgoing.text"
	LyricsText    = "lyrics.text"
	LinkOpen      = "link.open"
	MessageRender = "message.render"
)

// Buffers handed to the app are kept here until it frees them, so the GC never moves or collects them.
var pinned = map[uintptr][]byte{}

//export ayu_alloc
func ayuAlloc(length uint32) unsafe.Pointer {
	if length == 0 {
		length = 1
	}
	buffer := make([]byte, length)
	pointer := unsafe.Pointer(&buffer[0])
	pinned[uintptr(pointer)] = buffer
	return pointer
}

//export ayu_free
func ayuFree(pointer unsafe.Pointer, length uint32) {
	delete(pinned, uintptr(pointer))
}

func give(text string) uint64 {
	pointer := ayuAlloc(uint32(len(text)))
	copy(unsafe.Slice((*byte)(pointer), len(text)), text)
	return uint64(uintptr(pointer))<<32 | uint64(len(text))
}

func take(pointer unsafe.Pointer, length uint32) string {
	text := string(unsafe.Slice((*byte)(pointer), length))
	ayuFree(pointer, length)
	return text
}

// Request sends a JSON request to the app and returns its JSON answer.
func Request(message string) (string, bool) {
	if len(message) == 0 {
		return "", false
	}
	bytes := []byte(message)
	packed := host(unsafe.Pointer(&bytes[0]), uint32(len(bytes)))
	if packed == 0 {
		return "", false
	}
	return take(unsafe.Pointer(uintptr(packed>>32)), uint32(packed&0xffffffff)), true
}

func send(fields map[string]any) (string, bool) {
	data, err := json.Marshal(fields)
	if err != nil {
		return "", false
	}
	return Request(string(data))
}

// Log writes to the plugin console.
func Log(text string) { send(map[string]any{"op": "log", "level": "info", "text": text}) }

// Toast shows a short message in the app.
func Toast(text string) { send(map[string]any{"op": "toast", "text": text}) }

// Call runs any extended API (ui.menu.add, ui.overlay.create, net.fetch, …).
func Call(op string, args map[string]any) (map[string]any, bool) {
	fields := map[string]any{"op": op}
	for key, value := range args {
		fields[key] = value
	}
	answer, ok := send(fields)
	if !ok {
		return nil, false
	}
	var result map[string]any
	if json.Unmarshal([]byte(answer), &result) != nil {
		return nil, false
	}
	return result, true
}

// Storage keeps small values per plugin.
func StorageGet(key string) (string, bool) {
	result, ok := Call("storage.get", map[string]any{"key": key})
	if !ok {
		return "", false
	}
	value, ok := result["value"].(string)
	return value, ok
}

func StorageSet(key, value string) { Call("storage.set", map[string]any{"key": key, "value": value}) }

// Context is handed to text hooks.
type Context struct {
	PeerID string
	Raw    string
}

// TextHandler returns the new text, or nil to keep it.
type TextHandler func(text string, ctx Context) *string

var textHandlers []TextHandler
var eventHandlers = map[string][]func(payload string){}

func register(point, mode string, handler TextHandler) {
	textHandlers = append(textHandlers, handler)
	send(map[string]any{"op": "hook", "point": point, "mode": mode, "handler": len(textHandlers)})
}

func Before(point string, handler TextHandler)  { register(point, "before", handler) }
func After(point string, handler TextHandler)   { register(point, "after", handler) }
func Replace(point string, handler TextHandler) { register(point, "replace", handler) }

// On subscribes to an app event; the payload is JSON.
func On(event string, handler func(payload string)) {
	eventHandlers[event] = append(eventHandlers[event], handler)
	send(map[string]any{"op": "on", "event": event})
}

type dispatchMessage struct {
	Op      string `json:"op"`
	Handler int    `json:"handler"`
	Text    string `json:"text"`
	PeerID  any    `json:"peerId"`
	Event   string `json:"event"`
}

//export ayu_dispatch
func ayuDispatch(pointer unsafe.Pointer, length uint32) uint64 {
	raw := take(pointer, length)
	var message dispatchMessage
	if json.Unmarshal([]byte(raw), &message) != nil {
		return give("{}")
	}
	switch message.Op {
	case "hook":
		if message.Handler < 1 || message.Handler > len(textHandlers) {
			return give(`{"text":null}`)
		}
		peer := ""
		switch value := message.PeerID.(type) {
		case string:
			peer = value
		case float64:
			peer = strconv.FormatInt(int64(value), 10)
		}
		result := textHandlers[message.Handler-1](message.Text, Context{PeerID: peer, Raw: raw})
		if result == nil {
			return give(`{"text":null}`)
		}
		data, _ := json.Marshal(map[string]string{"text": *result})
		return give(string(data))
	case "event":
		for _, handler := range eventHandlers[message.Event] {
			handler(raw)
		}
	}
	return give("{}")
}
