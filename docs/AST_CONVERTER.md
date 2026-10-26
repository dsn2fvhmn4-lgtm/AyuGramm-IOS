# On-device AST converter, native plugin API 6

This source revision adds a second conversion path after the existing native
adapters and literal-hook converter. It is intended for the next IPA; Release 4
does not contain the embedded interpreter or API 6 evaluator.

## Import and activation

Open a `.plugin` from a chat or choose it in Settings → AyuGram → Plugins.
The app reads the complete source on a worker queue. Known adapters retain
priority. If the original literal template does not match, the embedded Python
parser converts supported source into a native JSON text program. The app shows
the name, author, version and installation confirmation before activating it.

The existing atomic installation path persists the program in the account's
settings. It runs in installation order alongside older plugins and survives
restart, disable/re-enable, export and re-import. Downloaded Python source is
never executed by this converter. It uses AST parsing rather than `exec`/`eval`.

## Mapped operations

- Direct `params.message` updates or one local text variable committed back to it.
- Chained string operations, comments, docstrings and ordinary type annotations.
- `replace` with optional replacement count, including deletion and expansion.
- `lower`, `upper` and argument-free `strip`.
- Literal prefix/suffix insertion, `removeprefix` and `removesuffix`.
- `if`/`elif`/`else`, including nested branches. Conditions support `startswith`,
  `endswith`, membership, equality/inequality and `not`. Each branch condition is
  evaluated once before its full block, so an earlier replacement cannot change
  which later statements in that block run.
- The common early-return guard for non-string `params.message` values. The
  native outgoing seam already excludes non-text messages.

The entire file must match the supported subset. Other imports, initialization
work, loops, request hooks, arbitrary functions, Java views, external packages and
Android DEX/JNI payloads are rejected rather than silently discarded. A general
Android plugin with arbitrary hooks is not converted by this block.

## Bounds and native execution

The source is at most 64 KB / 1024 lines / 4096 AST nodes. Native programs allow
64 instructions and four branch levels; literal operands are at most 128 UTF-8
bytes. Input/output is bounded to 8192 UTF-8 bytes and 4096 UTF-16 units. Empty or
oversized transformed output preserves the original text; there is no truncation.
Formatted/entity-bearing text, media captions, forwards and secret chats retain
their existing behavior. Existing native adapter behavior is unchanged.

The program uses API 6, so older versions reject it instead of ignoring the new
instructions. The source hash covers the original UTF-8 input, including line
endings. The exported JSON contains the program, not executable Python source.

## Build integration

`ci/python_support.py` downloads the official BeeWare Python 3.13-b15 iOS package
with a pinned SHA-256. Bazel links and embeds the selected device/simulator Python
framework. After the unsigned native build, the packaging step installs the
standard library, runtime sources and hook map. Binary standard-library modules
become nested frameworks with `.fwork`/`.origin` markers, following the upstream
PEP 730 layout; on macOS they receive ad-hoc signatures. The final installation
signer must sign every nested framework as well as the app. The artifact manifest
records the support version and hash. Python's license is retained in the bundle.

The preflight checks the real Objective-C implementation against the pinned
Python headers and iOS Simulator SDK. The actual Swift runtime and model sources
are included in SDK checks. Host tests exercise the persisted native program.
Desktop tests cover complete-file rejection, chained operations, branch output,
compiler dispatch and framework packaging. Local packaging checks use a control
archive and do not establish interpreter startup on an iPhone.

Example: [source plugin](../plugins/android_branch_hook.plugin) and
[converted native plugin](../plugins/android_branch_hook_ios.plugin).

The same compiler is available on a computer:

```sh
python tools/convert_plugin.py --ast plugins/android_branch_hook.plugin output.plugin
```

Upstream references: [Python Apple support](https://github.com/beeware/Python-Apple-support),
[Python on iOS](https://docs.python.org/3/using/ios.html).
