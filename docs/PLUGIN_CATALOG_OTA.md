# Updating supported plugins without another IPA

The base app includes a signed adapter catalog reader and an **Update plugin list**
button on the Plugins page. Install this base IPA once. Later, a developer can
publish a mapping for a supplied `.plugin` file in the GitHub catalog. The user
refreshes the list, imports that same original file, confirms installation, and
its mapped native functionality becomes available without another IPA.

## Import order

1. Native `.plugin` JSON, including verification of portable API 7 catalog proofs.
2. Exact original-file hash in the downloaded, verified catalog.
3. The original built-in reviewed adapters.
4. Existing literal-template and embedded AST conversion.

Catalog activation uses the existing transactional installation path. It does
not modify existing plugin choices or force an installed plugin replacement.
Installed programs and their author/name/version/proofs persist per account.
The catalog cache is app-wide and works offline after a successful refresh.

## Integrity and compatibility

Catalog and adapter signatures have separate signing domains. The native client
verifies Ed25519 signatures using its pinned CryptoKit public key. Each adapter
binds the complete native manifest and exact source hash. Portable proofs allow
export/re-import and re-enable without requiring the current server catalog.
String fields are compared through deterministic encoded bytes so Unicode
normalization cannot alter literal operations under someone else's signature.

The download uses HTTPS, an ephemeral cookie/credential-free session, no redirects,
45-second resource timeout and a 2 MB response cap. Decoded catalog payloads are
limited to 1 MB, 128 entries and 16 KB per adapter. The client validates every
compatible manifest before writing the catalog atomically. The previous snapshot
survives network, signature, schema and filesystem failures. Revision checks stop
rollback or conflicting same-revision publications.

API 7 reserves the portable-proof format; versions 1–6 remain compatible. Future
API entries are counted as requiring a newer app and are not activated. All mapped
actions still have their existing native scope/limits. Catalog data cannot add a
new native hook, operator, Android runtime or framework to an older IPA.

Publisher procedure and key storage: [plugin-catalog/README.md](../plugin-catalog/README.md).
