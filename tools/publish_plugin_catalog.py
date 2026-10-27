"""Publish signed, data-only native adapters. The signing key stays outside Git."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import time

MARKER = 'ayugram/catalog-v1'
FORMAT = 'ayugram-plugin-catalog-v1'
ADAPTER_DOMAIN = b'AyuGram adapter v1\0'
CATALOG_DOMAIN = b'AyuGram catalog v1\0'
MAX_MANIFEST_BYTES = 16384


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def validate_condition(value):
    if not isinstance(value, dict) or value.get('kind') not in {'prefix', 'suffix', 'contains', 'equals'}:
        raise ValueError('Unknown native text condition')
    if type(value.get('negated')) is not bool or not isinstance(value.get('value'), str) or len(value['value'].encode()) > 128:
        raise ValueError('Invalid native text condition')


def validate_program(program):
    if not isinstance(program, dict) or set(program) != {'instructions'}:
        raise ValueError('Invalid native text program')
    remaining = [64]
    def block(instructions, depth=0):
        if not isinstance(instructions, list) or not instructions or depth > 4:
            raise ValueError('Native programs need 1...64 instructions and at most four branch levels')
        for item in instructions:
            remaining[0] -= 1
            if remaining[0] < 0 or not isinstance(item, dict):
                raise ValueError('Too many native program instructions')
            op = item.get('op')
            if op == 'branch':
                if set(item) - {'op', 'condition', 'body', 'otherwise'}:
                    raise ValueError('Unexpected branch operands')
                validate_condition(item.get('condition'))
                block(item.get('body'), depth + 1)
                if item.get('otherwise') is not None:
                    if not isinstance(item['otherwise'], list):
                        raise ValueError('Invalid else branch')
                    if item['otherwise']:
                        block(item['otherwise'], depth + 1)
            elif op in {'lower', 'upper', 'strip'}:
                if set(item) != {'op'}:
                    raise ValueError('Unexpected string-operation operands')
            elif op in {'prepend', 'append', 'removePrefix', 'removeSuffix', 'replace'}:
                if not isinstance(item.get('value'), str) or len(item['value'].encode()) > 128:
                    raise ValueError('Invalid string operand')
                if op == 'replace':
                    if set(item) - {'op', 'find', 'value', 'count'} or not isinstance(item.get('find'), str) or not item['find'] or len(item['find'].encode()) > 128:
                        raise ValueError('Invalid replacement pattern')
                    if 'count' in item and (type(item['count']) is not int or not 0 <= item['count'] <= 4096):
                        raise ValueError('Invalid replacement count')
                elif set(item) != {'op', 'value'} or not item['value']:
                    raise ValueError('Invalid prefix/suffix operation')
            else:
                raise ValueError('Native operation needs an IPA update: ' + str(op))
    block(program.get('instructions'))


def native_manifest(value, source=None):
    value = {k: v for k, v in value.items() if k in {'format', 'apiVersion', 'id', 'name', 'author', 'version', 'summary', 'actions', 'sourceSHA256', 'convertedFrom', 'limitations'}}
    value.pop('catalogProof', None)
    value['apiVersion'] = 9 if any(a.get('kind') == 'formattedCopy' for a in value.get('actions', [])) else 8 if any(a.get('kind') in {'groupMentions', 'petpet', 'reactionsTotal', 'formattedCopy'} for a in value.get('actions', [])) else 7
    value['convertedFrom'] = MARKER
    if source is not None:
        value['sourceSHA256'] = hashlib.sha256(source).hexdigest()
    if value.get('format') != 'ayugram-ios-plugin':
        raise ValueError('Expected a native ayugram-ios-plugin adapter')
    for field in ('id',):
        if not re.fullmatch(r'[a-z0-9_-]{1,64}', value.get(field, '')):
            raise ValueError('Invalid adapter ' + field)
    if not re.fullmatch(r'[0-9a-f]{64}', value.get('sourceSHA256', '')):
        raise ValueError('Adapter must identify the exact original plugin SHA-256')
    for field, maximum in [('name', 64), ('author', 128), ('version', 32), ('summary', 2048)]:
        text = value.get(field)
        if not isinstance(text, str) or len(text) > maximum or (field != 'summary' and not text):
            raise ValueError('Invalid adapter ' + field)
    actions = value.get('actions')
    if not isinstance(actions, list) or not 1 <= len(actions) <= 8:
        raise ValueError('Adapter needs 1...8 native actions')
    allowed = {'search', 'searchTerms', 'replaceText', 'outgoingReplace', 'cameraFlip', 'chatColors', 'arcadeGame', 'unlimitedAccounts', 'groupMentions', 'petpet', 'reactionsTotal', 'formattedCopy'}
    ids = set()
    for action in actions:
        if action.get('kind') not in allowed or not re.fullmatch(r'[a-z0-9_-]{1,64}', action.get('id', '')):
            raise ValueError('Adapter uses an unknown native action')
        if action['id'] in ids:
            raise ValueError('Duplicate native action ID')
        ids.add(action['id'])
        if not isinstance(action.get('title'), str) or not 0 < len(action['title']) <= 80:
            raise ValueError('Invalid action title')
        if action.get('program') is not None:
            if action['kind'] != 'outgoingReplace' or any(action.get(k) is not None for k in ('find', 'replacement', 'prefix', 'condition', 'replacementCount')):
                raise ValueError('Native programs cannot mix with literal replacement fields')
            validate_program(action['program'])
        elif action['kind'] in {'replaceText', 'outgoingReplace'}:
            find, replacement = action.get('find'), action.get('replacement')
            if not isinstance(find, str) or not find or len(find.encode()) > 128 or not isinstance(replacement, str) or len(replacement.encode()) > 128:
                raise ValueError('Invalid literal replacement')
            if action['kind'] == 'outgoingReplace':
                if not replacement or len(replacement.encode()) > len(find.encode()) or len(replacement.encode('utf-16-le')) > len(find.encode('utf-16-le')):
                    raise ValueError('Expanding replacements must use a bounded native program')
                if action.get('condition') is not None:
                    validate_condition(action['condition'])
                if action.get('prefix') is not None and (not isinstance(action['prefix'], str) or len(action['prefix'].encode()) > 128 or action.get('condition') is not None):
                    raise ValueError('Invalid replacement prefix')
                if action.get('replacementCount') is not None and (type(action['replacementCount']) is not int or not 0 <= action['replacementCount'] <= 4096):
                    raise ValueError('Invalid replacement count')
            elif any(action.get(k) is not None for k in ('prefix', 'condition', 'replacementCount')):
                raise ValueError('Draft replacement does not use outgoing-hook conditions')
        elif any(action.get(k) is not None for k in ('find', 'replacement', 'prefix', 'condition', 'replacementCount')):
            raise ValueError('Unexpected text operands on a native action')
        if action['kind'] == 'arcadeGame' and action['id'] not in {'game_2048', 'game_flappy', 'game_dino'}:
            raise ValueError('New games need a native game implementation')
    value.setdefault('limitations', [])
    if not isinstance(value['limitations'], list) or len(value['limitations']) > 16 or any(not isinstance(t, str) or len(t) > 512 for t in value['limitations']):
        raise ValueError('Invalid adapter limitations')
    if len(encode(value)) > MAX_MANIFEST_BYTES:
        raise ValueError('Adapter exceeds 16 KB')
    return value


def signing_key(path, initialize=False):
    # Publisher-only dependency. No third-party crypto package is needed by CI
    # compilation or the iOS client, which verifies with Apple's CryptoKit.
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    path = Path(path)
    if initialize:
        key = Ed25519PrivateKey.generate()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as output:
            output.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        path.chmod(0o600)
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError('Expected an Ed25519 catalog signing key')
    return key


def public_bytes(key):
    from cryptography.hazmat.primitives import serialization
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def package(manifests, key, revision):
    if not 1 <= revision <= 2147483647 or len(manifests) > 128:
        raise ValueError('Invalid catalog revision or adapter count')
    seen = set()
    adapters = []
    for value in manifests:
        value = native_manifest(value)
        source_hash = value['sourceSHA256']
        if source_hash in seen:
            raise ValueError('Duplicate original plugin hash')
        seen.add(source_hash)
        data = encode(value)
        adapters.append({'manifestData': base64.b64encode(data).decode(), 'signature': base64.b64encode(key.sign(ADAPTER_DOMAIN + data)).decode()})
    payload = encode({'revision': revision, 'createdAt': int(time.time()), 'adapters': adapters})
    if len(payload) > 1024 * 1024:
        raise ValueError('Catalog payload exceeds 1 MB')
    return {'format': FORMAT, 'payload': base64.b64encode(payload).decode(), 'signature': base64.b64encode(key.sign(CATALOG_DOMAIN + payload)).decode()}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key', type=Path, required=True)
    parser.add_argument('--init-key', action='store_true')
    parser.add_argument('--public-key', type=Path, default=Path('plugin-catalog/public-key.txt'))
    parser.add_argument('--adapters', type=Path, default=Path('plugin-catalog/adapters'))
    parser.add_argument('--catalog', type=Path, default=Path('plugin-catalog/catalog.json'))
    parser.add_argument('--source', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--revision', type=int)
    args = parser.parse_args()
    key = signing_key(args.key, args.init_key)
    public = base64.b64encode(public_bytes(key)).decode()
    if args.public_key.exists() and args.public_key.read_text().strip() != public:
        raise SystemExit('Signing key differs from the pinned public key; keep the existing key')
    args.public_key.parent.mkdir(parents=True, exist_ok=True)
    args.public_key.write_bytes((public + '\n').encode())
    if args.source is not None or args.manifest is not None:
        if args.source is None or args.manifest is None:
            raise SystemExit('--source and --manifest must be used together')
        value = native_manifest(json.loads(args.manifest.read_text(encoding='utf-8')), args.source.read_bytes())
        write_json(args.adapters / (value['sourceSHA256'] + '.json'), value)
    manifests = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(args.adapters.glob('*.json'))]
    previous = 0
    if args.catalog.exists():
        envelope = json.loads(args.catalog.read_text(encoding='utf-8'))
        previous = json.loads(base64.b64decode(envelope['payload']))['revision']
    revision = args.revision if args.revision is not None else previous + 1
    if revision <= previous:
        raise SystemExit('A published catalog revision must increase')
    write_json(args.catalog, package(manifests, key, revision))
    print('Published catalog revision', revision, 'with', len(manifests), 'adapters; signing key was not exported')


if __name__ == '__main__':
    main()
