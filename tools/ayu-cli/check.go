package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

// Permissions the app knows (AyuPluginPermission plus the 27.5 additions).
var knownPermissions = map[string]string{
	"ui": "alerts and sheets", "menu": "message menu items", "profile": "profile blocks and buttons",
	"overlay": "overlays", "fonts": "font sizes", "badges": "chat badges", "clipboard": "clipboard (write)",
	"device": "device information", "haptics": "haptics", "network": "network (domains from @connect)",
	"messages": "send, edit and react", "messages.read": "read messages (dangerous)", "ai": "AI completion",
	"secrets": "Keychain secrets", "composer": "composer buttons", "notifications": "notification hook",
	"links": "link rewriting", "screens": "custom pages", "commands": "dot commands",
}

var idPattern = regexp.MustCompile(`^[a-z0-9_-]{1,64}$`)

type checkReport struct {
	File        string
	Language    string
	Fields      map[string]string
	Permissions []string
	Domains     []string
	SHA256      string
	Size        int
	Problems    []string
	Notes       []string
}

func (r checkReport) print() {
	fmt.Printf("%s  (%s, %d bytes)\nsha256 %s\n", r.File, r.Language, r.Size, r.SHA256)
	keys := make([]string, 0, len(r.Fields))
	for key := range r.Fields {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		fmt.Printf("  %-12s %s\n", key, r.Fields[key])
	}
	for _, permission := range r.Permissions {
		fmt.Printf("  permission   %s — %s\n", permission, knownPermissions[permission])
	}
	for _, domain := range r.Domains {
		fmt.Printf("  connect      %s\n", domain)
	}
	for _, note := range r.Notes {
		fmt.Println("  note:", note)
	}
	for _, problem := range r.Problems {
		fmt.Println("  PROBLEM:", problem)
	}
	if len(r.Problems) == 0 {
		fmt.Println("OK")
	}
}

func checkPlugin(path string) (checkReport, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return checkReport{}, err
	}
	sum := sha256.Sum256(data)
	report := checkReport{File: filepath.Base(path), SHA256: hex.EncodeToString(sum[:]), Size: len(data), Fields: map[string]string{}}
	if len(data) > 2<<20 {
		report.Problems = append(report.Problems, "larger than the 2 MB install limit")
	}
	if len(data) >= 4 && string(data[:4]) == "\x00asm" {
		report.Language = "WebAssembly"
		exports, imports, manifest, err := wasmExportsAndImports(data)
		if err != nil {
			report.Problems = append(report.Problems, err.Error())
			return report, nil
		}
		for _, name := range []string{"ayu_init", "ayu_dispatch", "ayu_alloc", "ayu_free", "memory"} {
			if !contains(exports, name) {
				report.Problems = append(report.Problems, "missing export "+name)
			}
		}
		for _, name := range imports {
			if name != "ayu.host" && !strings.HasPrefix(name, "wasi_snapshot_preview1.") {
				report.Problems = append(report.Problems, "import the app does not provide: "+name)
			}
		}
		if manifest == nil {
			report.Problems = append(report.Problems, "no ayu.manifest section (use `ayu pack`)")
			return report, nil
		}
		var fields map[string]any
		if err := json.Unmarshal(manifest, &fields); err != nil {
			report.Problems = append(report.Problems, "ayu.manifest is not JSON")
			return report, nil
		}
		for key, value := range fields {
			switch typed := value.(type) {
			case string:
				report.Fields[key] = typed
			case []any:
				parts := make([]string, 0, len(typed))
				for _, item := range typed {
					parts = append(parts, fmt.Sprint(item))
				}
				report.Fields[key] = strings.Join(parts, ", ")
			default:
				report.Fields[key] = fmt.Sprint(typed)
			}
		}
	} else {
		text := string(data)
		prefix := "//"
		report.Language = "JavaScript"
		switch strings.ToLower(filepath.Ext(path)) {
		case ".py":
			prefix, report.Language = "#", "Python"
		case ".ts":
			report.Language = "TypeScript"
		}
		lines := strings.Split(text, "\n")
		if len(lines) > 80 {
			lines = lines[:80]
		}
		for _, line := range lines {
			trimmed := strings.TrimSpace(line)
			if !strings.HasPrefix(trimmed, prefix) {
				continue
			}
			trimmed = strings.TrimSpace(strings.TrimPrefix(trimmed, prefix))
			if !strings.HasPrefix(trimmed, "@") {
				continue
			}
			key, value, _ := strings.Cut(trimmed[1:], " ")
			report.Fields[key] = strings.TrimSpace(value)
		}
	}
	if id := report.Fields["id"]; !idPattern.MatchString(id) {
		report.Problems = append(report.Problems, "@id must be 1–64 of a-z, 0-9, - and _")
	}
	for _, key := range []string{"name", "version"} {
		if report.Fields[key] == "" {
			report.Problems = append(report.Problems, "missing @"+key)
		}
	}
	for _, permission := range splitList(report.Fields["permissions"]) {
		if _, ok := knownPermissions[permission]; !ok {
			report.Problems = append(report.Problems, "unknown permission "+permission)
		}
		report.Permissions = append(report.Permissions, permission)
	}
	for _, domain := range splitList(report.Fields["connect"]) {
		if strings.Contains(domain, "/") || strings.Contains(domain, "*") && !strings.HasPrefix(domain, "*.") {
			report.Problems = append(report.Problems, "@connect takes host names like api.example.com or *.example.com: "+domain)
		}
		report.Domains = append(report.Domains, domain)
	}
	if len(report.Domains) > 0 && !contains(report.Permissions, "network") {
		report.Problems = append(report.Problems, "@connect needs the network permission")
	}
	if report.Fields["inject"] == "true" {
		report.Notes = append(report.Notes, "injecting plugin: installs only with an official signature or the developer option")
	}
	return report, nil
}

func splitList(value string) []string {
	var out []string
	for _, item := range strings.FieldsFunc(value, func(r rune) bool { return r == ',' || r == ' ' }) {
		out = append(out, strings.ToLower(item))
	}
	return out
}

func contains(list []string, value string) bool {
	for _, item := range list {
		if item == value {
			return true
		}
	}
	return false
}
