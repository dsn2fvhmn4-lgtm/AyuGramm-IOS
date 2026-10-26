"""Validate exported native sources before invoking any SDK checks."""
import json
from pathlib import Path


def missing_port_sources(source, manifest=None):
    if manifest is None:
        manifest = Path(__file__).with_name('required_port_sources.json')
    required = json.loads(Path(manifest).read_text(encoding='utf-8'))
    return [name for name in required if not (Path(source) / name).is_file()]
