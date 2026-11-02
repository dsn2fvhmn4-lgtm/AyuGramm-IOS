package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

var templates = map[string]struct {
	file string
	body string
}{
	"js": {"%s.js", `// @id %[1]s
// @name %[2]s
// @author you
// @version 1.0
// @description What it does
// @permissions menu

ayu.ui.menu.add({ id: 'count', title: 'Count characters' });
ayu.on('menuAction', ({ itemId, text }) => {
  if (itemId === 'count') ayu.toast(String([...text].length) + ' characters');
});
`},
	"ts": {"%s.ts", `// @id %[1]s
// @name %[2]s
// @author you
// @version 1.0
// @description What it does
/// <reference path="ayu.d.ts" />

ayu.hooks.before(ayu.hooks.points.outgoingText, (text: string): string | undefined =>
  text.endsWith('!!') ? text.toUpperCase() : undefined);
`},
	"py": {"%s.py", `# @id %[1]s
# @name %[2]s
# @author you
# @version 1.0
# @description What it does

def shout(text, ctx):
    if text.endswith('!!'):
        return text.upper()
    return None

ayu.hooks.before('message.outgoing.text', shout)
`},
	"rust": {"%s.rs", `use ayugram_plugin::{hooks, log, manifest};

manifest!(br#"{"id":"%[1]s","name":"%[2]s","author":"you","version":"1.0","description":"What it does"}"#);

#[no_mangle]
pub extern "C" fn ayu_init() {
    hooks::before(hooks::OUTGOING_TEXT, |text, _ctx| {
        text.ends_with("!!").then(|| text.to_uppercase())
    });
    log("loaded");
}
`},
	"zig": {"%s.zig", `// @manifest {"id":"%[1]s","name":"%[2]s","author":"you","version":"1.0","description":"What it does"}
const ayu = @import("ayu.zig");
const std = @import("std");

fn shout(text: []const u8, ctx: ayu.Context) ?[]const u8 {
    _ = ctx;
    if (!std.mem.endsWith(u8, text, "!!")) return null;
    return ayu.upper(text);
}

export fn ayu_init() void {
    ayu.hooks.before(ayu.hooks.outgoing_text, shout);
    ayu.log("loaded");
}
`},
	"as": {"%s.as.ts", `// @manifest {"id":"%[1]s","name":"%[2]s","author":"you","version":"1.0","description":"What it does"}
export { ayu_alloc, ayu_free, ayu_dispatch } from "./ayu";
import { log, before, OUTGOING_TEXT } from "./ayu";

export function ayu_init(): void {
  before(OUTGOING_TEXT, (text: string, peerId: string): string | null =>
    text.endsWith("!!") ? text.toUpperCase() : null);
  log("loaded");
}
`},
	"go": {"%s.go", `// @manifest {"id":"%[1]s","name":"%[2]s","author":"you","version":"1.0","description":"What it does"}
package main

import (
	"strings"

	"github.com/murk-sus/ayugram-sdk/ayu"
)

//export ayu_init
func ayuInit() {
	ayu.Before(ayu.OutgoingText, func(text string, ctx ayu.Context) *string {
		if !strings.HasSuffix(text, "!!") {
			return nil
		}
		upper := strings.ToUpper(text)
		return &upper
	})
	ayu.Log("loaded")
}

func main() {}
`},
}

func scaffold(name, language string) error {
	template, ok := templates[language]
	if !ok {
		return fmt.Errorf("unknown language %q (js, ts, py, rust, zig, as, go)", language)
	}
	id := strings.ToLower(strings.Map(func(r rune) rune {
		if r >= 'a' && r <= 'z' || r >= 'A' && r <= 'Z' || r >= '0' && r <= '9' || r == '-' || r == '_' {
			return r
		}
		return '-'
	}, name))
	file := fmt.Sprintf(template.file, id)
	if _, err := os.Stat(file); err == nil {
		return fmt.Errorf("%s already exists", file)
	}
	if err := os.WriteFile(file, []byte(fmt.Sprintf(template.body, id, name)), 0o644); err != nil {
		return err
	}
	fmt.Printf("created %s\n", filepath.Clean(file))
	switch language {
	case "js", "py":
		fmt.Println("next: ayu check " + file + " && ayu dev " + file)
	case "ts":
		fmt.Println("next: copy sdk/typescript/ayu.d.ts here, build with esbuild, or send the .ts to the cloud build")
	default:
		fmt.Println("next: build with the SDK in sdk/, then `ayu pack` and `ayu check` (or use the cloud build)")
	}
	return nil
}
