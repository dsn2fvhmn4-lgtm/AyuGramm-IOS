"""Package reviewed Android sources as iOS cards/adapters. Never executes plugin code."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 8 * 1024 * 1024
CARD_LIMIT = 64 * 1024


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def signed_adapters(catalog):
    payload = json.loads(base64.b64decode(catalog["payload"], validate=True))
    result = {}
    for proof in payload["adapters"]:
        manifest = json.loads(base64.b64decode(proof["manifestData"], validate=True))
        if manifest.get("convertedFrom") != "ayugram/catalog-v1":
            raise ValueError("Unexpected adapter origin")
        manifest["catalogProof"] = proof
        result[manifest["sourceSHA256"]] = manifest
    return result


def package(source, destination, registry=None, catalog=None):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_dir() or source == destination or source in destination.parents:
        raise ValueError("Choose a separate output folder outside the source folder")
    registry = read_json(ROOT / "plugins/iosplug-support.json") if registry is None else registry
    catalog = read_json(ROOT / "plugin-catalog/catalog.json") if catalog is None else catalog
    adapters = signed_adapters(catalog)
    files = sorted(source.glob("*.plugin"), key=lambda path: (len(path.name), path.name))
    if len(files) > 256:
        raise ValueError("At most 256 source files per batch")
    groups = {}
    for path in files:
        if not 0 < path.stat().st_size <= LIMIT:
            raise ValueError("Source exceeds analysis limit: " + path.name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        groups.setdefault(digest, []).append(path.name)
    # Exclusive folder creation prevents overwriting a previous publication.
    destination.mkdir(parents=True, exist_ok=False)
    rows = []
    for digest, names in sorted(groups.items(), key=lambda item: item[1][0]):
        known = registry["sources"].get(digest, {})
        row = {"source": names[0], "duplicates": names[1:], "sha256": digest}
        if known.get("native"):
            card = {"format": "ayu-iosplug-1", **known["native"]}
            filename = card["id"] + ".iosplug"
            row.update(status="native_ios_port", minimum_app=known["minimum_app"], limitations=known["limitations"])
        elif digest in adapters:
            manifest = adapters[digest]
            card = {"format": "ayu-iosplug-2", "minimumEngineVersion": 2, "adapter": manifest}
            filename = manifest["id"] + ".iosplug"
            row.update(status="reviewed_native_adapter", minimum_app="iosplug engine 2", limitations=manifest["limitations"])
        else:
            required = known.get("required_entrypoints", [])
            if isinstance(required, str):
                required = [required]
            if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
                raise ValueError("Invalid entrypoint notes for " + names[0])
            row.update(status="not_ported", reason=known.get("reason", "Unknown source version: native implementation must be reviewed."),
                       required_entrypoints=required)
            rows.append(row)
            continue
        if Path(filename).name != filename or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_-." for c in filename):
            raise ValueError("Invalid package id")
        data = (json.dumps(card, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(data) > CARD_LIMIT:
            raise ValueError("Package exceeds device import limit: " + filename)
        with (destination / filename).open("xb") as output:
            output.write(data)
        row["file"] = filename
        rows.append(row)
    report = {"format": "ayu-iosplug-batch-report-1", "unique_sources": len(rows),
              "package_count": sum("file" in row for row in rows), "device_verification": "not_performed", "plugins": rows}
    (destination / "compatibility.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Плагины AyuGram iOS", "", "`.iosplug` включает встроенные iOS-функции; Python/Android-код не запускается.",
             "Для пакетов `ayu-iosplug-2`, Pill Labels и Mini Avatar нужна IPA с этим обновлением движка.",
             "Первые пять встроенных карточек v1 совместимы с прежней IPA, содержащей соответствующий плагин.",
             "Импорт: Плагины → + → файл .iosplug → подтвердить установку. Проверка на iPhone ещё не выполнена.",
             "", "Ни один пакет не обещает полный паритет с Android. Ограничения перечислены ниже.", ""]
    for row in rows:
        lines.append("## " + row["source"])
        if "file" in row:
            lines.append("Файл: `" + row["file"] + "`. База: " + row["minimum_app"] + ".")
            lines.extend("- " + text for text in row["limitations"])
        else:
            lines.append("Не перенесён: " + row["reason"])
            lines.extend("- Нужна точка входа: " + str(text) for text in row["required_entrypoints"])
        lines.append("")
    (destination / "README-RU.md").write_text("\n".join(lines), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    result = package(arguments.source, arguments.destination)
    print(f"{result['package_count']} .iosplug packages / {result['unique_sources']} unique sources")
