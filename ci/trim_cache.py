"""Bound only disposable Bazel cache entries to the personal Codemagic quota."""
import os
from pathlib import Path

root = Path(os.environ['CM_BUILD_DIR']).resolve() / '.ayu-temp' / 'ayu-bazel-cache'
if root.is_dir() and not root.is_symlink():
    entries = []
    for path in root.rglob('*'):
        if path.is_file() and not path.is_symlink():
            stat = path.stat()
            entries.append((stat.st_mtime, path, stat.st_size))
    size = sum(entry[2] for entry in entries)
    # Missing CAS entries are cache misses. Never trim workspace outputs or credentials.
    for _, path, length in sorted(entries):
        if size <= 2_500_000_000:
            break
        path.unlink(missing_ok=True)
        size -= length
    print(f'Bazel disk cache retained: {size / 1_000_000_000:.2f} GB')
