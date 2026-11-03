// Command ayu is the VoidGram for iOS plugin developer tool.
//
//	ayu dev <plugin file> [-port 8765]       hot reload: VoidGram (Tools → Hot reload) reinstalls on save
//	ayu pack <in.wasm> <manifest.json> <out> add or replace the `ayu.manifest` section of a WebAssembly plugin
//	ayu check <plugin file>                  validate the header, permissions, domains and WebAssembly exports
//	ayu new <name> [-lang js|ts|py|rust|zig|as|go]   create a plugin from a template
//	ayu sha <file>                           print the SHA-256 the catalog expects
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"flag"
	"fmt"
	"os"
	"strings"
)

const usage = `ayu — VoidGram for iOS plugin tool

  ayu dev <plugin file> [-port 8765]
  ayu pack <in.wasm> <manifest.json> <out.wasm>
  ayu check <plugin file>
  ayu new <name> [-lang js|ts|py|rust|zig|as|go]
  ayu sha <file>
`

func main() {
	if len(os.Args) < 2 {
		fmt.Print(usage)
		os.Exit(2)
	}
	command, rest := os.Args[1], os.Args[2:]
	var err error
	switch command {
	case "dev":
		set := flag.NewFlagSet("dev", flag.ExitOnError)
		port := set.Int("port", 8765, "WebSocket port")
		set.Parse(flagsFirst(rest))
		if set.NArg() != 1 {
			fail("usage: ayu dev <plugin file> [-port 8765]")
		}
		err = serveDev(set.Arg(0), *port)
	case "pack":
		if len(rest) != 3 {
			fail("usage: ayu pack <in.wasm> <manifest.json> <out.wasm>")
		}
		err = packManifest(rest[0], rest[1], rest[2])
	case "check":
		if len(rest) != 1 {
			fail("usage: ayu check <plugin file>")
		}
		var report checkReport
		report, err = checkPlugin(rest[0])
		if err == nil {
			report.print()
			if len(report.Problems) > 0 {
				os.Exit(1)
			}
		}
	case "new":
		set := flag.NewFlagSet("new", flag.ExitOnError)
		language := set.String("lang", "js", "js, ts, py, rust, zig, as or go")
		set.Parse(flagsFirst(rest))
		if set.NArg() != 1 {
			fail("usage: ayu new <name> [-lang js]")
		}
		err = scaffold(set.Arg(0), *language)
	case "sha":
		if len(rest) != 1 {
			fail("usage: ayu sha <file>")
		}
		var data []byte
		data, err = os.ReadFile(rest[0])
		if err == nil {
			sum := sha256.Sum256(data)
			fmt.Println(hex.EncodeToString(sum[:]))
		}
	default:
		fmt.Print(usage)
		os.Exit(2)
	}
	if err != nil {
		fail(err.Error())
	}
}

// flagsFirst moves "-name value" pairs before positional arguments, so flags work in any order.
func flagsFirst(args []string) []string {
	var flags, positional []string
	for i := 0; i < len(args); i++ {
		if strings.HasPrefix(args[i], "-") && len(args[i]) > 1 {
			flags = append(flags, args[i])
			if !strings.Contains(args[i], "=") && i+1 < len(args) {
				flags = append(flags, args[i+1])
				i++
			}
		} else {
			positional = append(positional, args[i])
		}
	}
	return append(flags, positional...)
}

func fail(message string) {
	fmt.Fprintln(os.Stderr, "ayu:", message)
	os.Exit(1)
}
