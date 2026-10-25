"""Surface a failed step's errors as GitHub annotations, which the run page shows without sign-in."""
import re
import sys
from pathlib import Path

MAX_LINES = 40


def escape(text):
    return text.replace('%', '%25').replace('\r', '').replace('\n', '%0A')


def main():
    title, paths = sys.argv[1], [Path(path) for path in sys.argv[2:]]
    for path in paths:
        if not path.is_file():
            continue
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
        errors = [line for line in lines if re.search(r'\berror\b|Error:|FAIL|Traceback|SystemExit', line)]
        # Compiler errors are most useful; otherwise fall back to the end of the log.
        selected = errors[:MAX_LINES] if errors else lines[-MAX_LINES:]
        if selected:
            print(f'::error title={escape(title)} ({escape(path.name)})::{escape(chr(10).join(selected))}')


if __name__ == '__main__':
    main()
