# OTA plugin adapters

The API 7 base IPA adds **Settings → AyuGram → Plugins → Update plugin list**.
After that one base installation, publishing another supported native adapter in
this directory does not require rebuilding or reinstalling the IPA.

The app downloads `catalog.json`, verifies its Ed25519 signature and atomically
retains the newest valid revision. Import matches the SHA-256 of the original
`.plugin` file and prepares its native manifest. Normal import confirmation still
applies; refreshing the catalog never installs or enables plugins by itself.

`adapters/*.json` are publisher inputs, not files to import directly. The signed
catalog wraps each adapter in a portable proof. Installed/exported plugins retain
that proof, so activation works offline even after a later catalog changes.

## Adding support for a supplied plugin

1. Inspect the original plugin and map its complete supported behavior to existing
   native actions or a bounded text program. Retain its author/name/version.
2. Create a native manifest JSON. Use only operations already in the base IPA.
3. Publish from the repository root:

```powershell
python tools/publish_plugin_catalog.py --key "..\.tools\plugin-catalog-signing.pem" --source "C:\path\original.plugin" --manifest "C:\path\adapter.json"
```

4. Commit and push **only the changed `plugin-catalog/` files**. Catalog-only
   commits do not match the native build workflow's path filters.
5. On the iPhone, tap **Update plugin list**, then import the original file.

The publisher requires the `cryptography` Python package. This is a publisher-only
dependency; app compilation and client verification use no extra crypto package.
Keep a secure backup of the signing key outside Git. The public key is pinned in
the base IPA; replacing that key requires distributing a new trusted base IPA.
The tool refuses to replace an existing key or sign with a different public key.

## Scope

Catalog entries can use existing search, draft/text operations, Camera Flip,
Chat Colors, Arcade Games and client account-limit actions. New native hooks,
new Swift operations, Android views/DEX/JNI and new frameworks require a base IPA
update. This mechanism downloads signed data, not executable Python or binaries.

`ota_lowercase_demo.plugin` is a concrete example: its helper method is outside
the built-in AST subset, but the catalog supplies the equivalent native lower-case
operation. Host checks import the same source before/after applying the catalog,
activate it, execute it, and restore/export it without network access.

Failed downloads/signatures/validation/writes keep the previous catalog. Older
revisions and conflicting contents under the same revision are rejected. The
client reports entries that require a newer app API. A new adapter for a changed
source file must use that changed file's exact hash.
