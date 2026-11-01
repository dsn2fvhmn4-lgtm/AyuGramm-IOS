package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
)

var wasmMagic = []byte{0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00}

func readLEB(data []byte, offset int) (uint64, int, error) {
	var value uint64
	var shift uint
	for i := offset; i < len(data) && i < offset+10; i++ {
		b := data[i]
		value |= uint64(b&0x7f) << shift
		if b&0x80 == 0 {
			return value, i + 1, nil
		}
		shift += 7
	}
	return 0, 0, errors.New("bad LEB128")
}

func writeLEB(value uint64) []byte {
	var out []byte
	for {
		b := byte(value & 0x7f)
		value >>= 7
		if value != 0 {
			out = append(out, b|0x80)
		} else {
			return append(out, b)
		}
	}
}

type wasmSection struct {
	id      byte
	name    string // custom sections only
	payload []byte // section contents without id and size
	start   int
	end     int
}

func parseSections(data []byte) ([]wasmSection, error) {
	if len(data) < 8 || !bytes.Equal(data[:8], wasmMagic) {
		return nil, errors.New("not a WebAssembly module")
	}
	var sections []wasmSection
	offset := 8
	for offset < len(data) {
		start := offset
		id := data[offset]
		size, next, err := readLEB(data, offset+1)
		if err != nil || next+int(size) > len(data) {
			return nil, errors.New("truncated section")
		}
		section := wasmSection{id: id, payload: data[next : next+int(size)], start: start, end: next + int(size)}
		if id == 0 {
			nameLength, nameStart, err := readLEB(section.payload, 0)
			if err == nil && nameStart+int(nameLength) <= len(section.payload) {
				section.name = string(section.payload[nameStart : nameStart+int(nameLength)])
			}
		}
		sections = append(sections, section)
		offset = section.end
	}
	return sections, nil
}

// packManifest adds the `ayu.manifest` custom section, replacing an existing one.
func packManifest(input, manifestPath, output string) error {
	data, err := os.ReadFile(input)
	if err != nil {
		return err
	}
	manifest, err := os.ReadFile(manifestPath)
	if err != nil {
		return err
	}
	var fields map[string]any
	if err := json.Unmarshal(manifest, &fields); err != nil {
		return fmt.Errorf("manifest is not JSON: %w", err)
	}
	for _, key := range []string{"id", "name", "version"} {
		if _, ok := fields[key].(string); !ok {
			return fmt.Errorf("manifest needs %q", key)
		}
	}
	sections, err := parseSections(data)
	if err != nil {
		return err
	}
	out := append([]byte{}, wasmMagic...)
	for _, section := range sections {
		if section.id == 0 && section.name == "ayu.manifest" {
			continue
		}
		out = append(out, data[section.start:section.end]...)
	}
	compact, _ := json.Marshal(fields)
	name := []byte("ayu.manifest")
	payload := append(writeLEB(uint64(len(name))), name...)
	payload = append(payload, compact...)
	out = append(out, 0)
	out = append(out, writeLEB(uint64(len(payload)))...)
	out = append(out, payload...)
	if err := os.WriteFile(output, out, 0o644); err != nil {
		return err
	}
	fmt.Printf("packed %s (%d bytes, manifest %s)\n", output, len(out), fields["id"])
	return nil
}

// wasmExportsAndImports lists export names and "module.name" imports.
func wasmExportsAndImports(data []byte) (exports []string, imports []string, manifest []byte, err error) {
	sections, err := parseSections(data)
	if err != nil {
		return nil, nil, nil, err
	}
	readName := func(payload []byte, offset int) (string, int, error) {
		length, next, err := readLEB(payload, offset)
		if err != nil || next+int(length) > len(payload) {
			return "", 0, errors.New("bad name")
		}
		return string(payload[next : next+int(length)]), next + int(length), nil
	}
	for _, section := range sections {
		switch section.id {
		case 0:
			if section.name == "ayu.manifest" {
				_, nameEnd, _ := readName(section.payload, 0)
				manifest = section.payload[nameEnd:]
			}
		case 2: // imports
			count, offset, err := readLEB(section.payload, 0)
			if err != nil {
				return nil, nil, nil, err
			}
			for i := uint64(0); i < count; i++ {
				module, next, err := readName(section.payload, offset)
				if err != nil {
					return nil, nil, nil, err
				}
				name, next, err := readName(section.payload, next)
				if err != nil {
					return nil, nil, nil, err
				}
				imports = append(imports, module+"."+name)
				kind := section.payload[next]
				next++
				switch kind {
				case 0: // function: type index
					_, next, err = readLEB(section.payload, next)
				case 1: // table: reftype + limits
					next++
					next, err = skipLimits(section.payload, next)
				case 2: // memory: limits
					next, err = skipLimits(section.payload, next)
				case 3: // global: valtype + mutability
					next += 2
				}
				if err != nil {
					return nil, nil, nil, err
				}
				offset = next
			}
		case 7: // exports
			count, offset, err := readLEB(section.payload, 0)
			if err != nil {
				return nil, nil, nil, err
			}
			for i := uint64(0); i < count; i++ {
				name, next, err := readName(section.payload, offset)
				if err != nil {
					return nil, nil, nil, err
				}
				exports = append(exports, name)
				_, next, err = readLEB(section.payload, next+1)
				if err != nil {
					return nil, nil, nil, err
				}
				offset = next
			}
		}
	}
	return exports, imports, manifest, nil
}

func skipLimits(payload []byte, offset int) (int, error) {
	if offset >= len(payload) {
		return 0, errors.New("bad limits")
	}
	flags := payload[offset]
	_, next, err := readLEB(payload, offset+1)
	if err != nil {
		return 0, err
	}
	if flags&1 != 0 {
		_, next, err = readLEB(payload, next)
	}
	return next, err
}
