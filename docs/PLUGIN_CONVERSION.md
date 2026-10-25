# Android hook templates and native import

This source revision adds **tap .plugin -> review -> Import and enable -> prepare
-> atomic commit**. It is not a universal Android runtime. Release 3's published
IPA is unchanged; native compilation and iPhone testing remain pending.

## Opening and applying

- Tap a downloaded, ordinary cloud-chat `.plugin` attachment. The native file
  opening path directs it to plugin import rather than generic document preview.
  Missing/incomplete cache data produces a download prompt after a bounded wait.
- Files can also use the app's registered `.plugin` document type, or be selected
  through **AyuGram Preferences -> Plugins -> Import .plugin**.
- Analysis reads a bounded file without executing it. The confirmation shows
  name, author, version, actions, permissions and conversion limitations.
- **Import and enable** performs local compatibility checks and prepares typed
  native actions off the UI thread. Only success replaces and enables the plugin
  in one settings transaction. Failure preserves the previous installation.
- A changed installation invalidates an older pending confirmation. During the
  short apply operation, the native navigation modal prevents interactive dismissal.
- Enabled state, metadata, native rules and their order survive restart and export.
  Disabling/removing a plugin stops its automatic rules for subsequent enqueue calls.
  Messages already queued are not reverted.

## Android mechanisms examined

References: exteraGram's [plugin lifecycle and outgoing hooks](https://plugins.exteragram.app/docs/plugin-class)
and [Xposed method hooks](https://plugins.exteragram.app/docs/xposed-hooking).

| Android pattern | Current iOS mapping |
| --- | --- |
| BasePlugin lifecycle and add_on_send_message_hook | Enabled per-account registry, read by the native enqueue path |
| Literal params.message.replace(old, new) | Typed outgoingReplace action, before ordinary cloud-text enqueue |
| One startswith/endswith/in/== guard, with not/not in/!= support | Literal native condition, evaluated once before the single guarded replacement |
| Literal replace(old, new, count) | Bounded native count from 0 to 4096; nonoverlapping matches in the original input |
| HookResult MODIFY with params | The returned native message retains its original attributes, reply/thread data and other enqueue fields |
| Type annotations using typing.Any/int/HookResult | Recognized type-only syntax in the supplied typed template |
| Direct MethodHook / Java reflection / Android views | No general conversion; a dedicated native mapping is required |
| Arbitrary imports, dependencies, settings callbacks or extra statements | Whole-file conversion is rejected rather than quietly dropping behavior |

## Automatically supported source templates

Examples, each still using the `.plugin` extension:

- [Literal outgoing hook](../plugins/android_literal_hook.plugin).
- [Prefix-conditional hook](../plugins/android_prefix_hook.plugin).
- [Annotated outgoing hook](../plugins/android_typed_hook.plugin).

These are functional source templates, not fixed file hashes. Metadata and literal
rules can vary within native limits. The on-device converter tokenizes the entire
file, checks method bodies and indentation, and accepts only the supported grammar.
One unconditional hook may contain up to eight replacements. A conditional hook
supports one replacement, so its original guard semantics are retained. Conditions
include `startswith`, `endswith`, literal `in`/`not in`, `==`/`!=`, and optional
unary `not`. Nested or compound conditions remain unsupported. A third literal
integer argument to `replace` is supported from 0 to 4096 (zero is a no-op).
Negative counts, expressions and boolean counts are rejected. Prefix and condition
fields are mutually exclusive; older prefix-only native files remain supported.
Manifests using a condition or replacement count declare API version 2. Older
clients reject that version instead of ignoring the new fields and changing behavior.
Existing API-1 files keep their previous semantics.
Comments/blank lines and either simple quote style are accepted. The accepted
escapes are newline, carriage return, tab, backslash and quote escapes.

No plugin source is imported into Python, Java, Xposed or a native dynamic library.
There is no remote code-generation service. Recognized files convert locally
without the owner editing code or using the desktop tool. For unsupported files,
the importer reports a source line and stops; it does not enable an empty or
partially guessed plugin. The separately reviewed Search+ 2.6.1 adapter remains
available with its previously documented partial feature scope.

## Automatic text-hook scope

The native enqueue integration applies only to **plain cloud text**, without media
or nonempty text-entity attributes. Formatted/entity-bearing text (including
automatically linked text), media captions, secret chats, inline stickers and native
forwards are unchanged. This scope is displayed before import.

Rules must have a nonempty find/replacement and must not increase UTF-8 or UTF-16
length. This bounds output without truncation, breaking entity offsets or sending
an empty replacement. Matching is literal and preserves code-unit distinctions;
prefix/suffix tests are anchored. A counted replacement scans the original input
left to right and never searches its own replacement output. Enabled plugins run in persisted installation order,
and rules inside each plugin retain source order. Settings belong to the sending
account, including background accounts. The permission is
`messages.outgoing.modify` and means automatic modification when the owner sends
eligible text; it does not grant arbitrary network or file access.

## Desktop tooling and verification

`tools/convert_plugin.py input.plugin output.plugin` additionally uses a static
Python AST implementation to recognize the source patterns. It does not execute
plugin code and never overwrites the original. The desktop AST parser accepts
some equivalent formatting that the stricter on-device line grammar may reject.
The `.expected.json` fixture files are generated by that independent parser.

The actual Swift host harness receives the repository's `plugins` directory and
compares the on-device converter's results with those AST fixtures. It tests
automatic replacement, prefix behavior, disabled hooks, whole-file rejection and
atomic failure. The extended matrix adds 19 source cases with 92 expected
behavior results, including empty/negated predicates, Unicode, zero counts,
nonoverlapping matches and persistence. These native tests run in Codemagic's existing model-test step.
The fast iOS SDK harness includes the actual converter model and plugin manager.

Windows tests cover the AST implementation, source contracts and patch integrity.
They do not prove that the full app compiles or that iPhone behavior is correct.
Before release, test attachment taps and Files opening, consent/cancel/replacement,
plain text versus links/formatting/media/secret/forward exclusions, multiple rules,
account switching, persistence, disable/remove, network conditions and queued text.
Inspect recorded simulator frames for the import and plugin-settings flows.

## Remaining compatibility work

This revision extends text-hook templates; it does not convert every plugin.
Android plugins can call arbitrary Java methods, render Android Views, intercept
Telegram request/update classes, access third-party packages or use platform
services. Each such dependency needs an implemented iOS bridge with matching
behavior and a device test. Accepting the file or copying metadata is not feature
compatibility. Unsupported statements reject the entire source and preserve the
installed version.

Future bridge families: request/update interception, settings/storage callbacks,
menus and native views, external libraries, timers and application lifecycle.
These families are a roadmap, not implemented APIs. Search+ still has its
separately disclosed partial scope. No current source or released IPA should be
advertised as supporting all exteraGram plugins.
