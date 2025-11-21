# python
from pathlib import Path
import json
import tempfile
import os
import sys

SCRIPT_PATH = Path(__file__).resolve()
SOURCE_PATH = SCRIPT_PATH.parent.parent / 'data/houses_clean.jsonl'

def is_days_equal_100(value) -> bool:
    try:
        return float(value) == 100.0
    except (TypeError, ValueError):
        return False

def main():
    if not SOURCE_PATH.exists():
        print(f"Source file not found: `{SOURCE_PATH}`", file=sys.stderr)
        sys.exit(1)

    total = 0
    removed = 0
    tmp_fd, tmp_path = tempfile.mkstemp(dir=SOURCE_PATH.parent, suffix='.tmp.jsonl')
    os.close(tmp_fd)  # will reopen with regular file IO

    with SOURCE_PATH.open('r', encoding='utf-8') as src, open(tmp_path, 'w', encoding='utf-8') as dst:
        for line in src:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                # skip malformed lines but keep count
                dst.write(line + '\n')
                continue

            if is_days_equal_100(obj.get('days_on_marked')):
                removed += 1
                continue  # drop this record
            dst.write(json.dumps(obj, ensure_ascii=False) + '\n')

    if removed > 0:
        # atomic replace
        os.replace(tmp_path, SOURCE_PATH)
        print(f"Rewrote `{SOURCE_PATH}`: removed {removed} of {total} records (kept {total - removed}).")
    else:
        # no changes, remove temporary file
        os.remove(tmp_path)
        print(f"No records with `days_on_marked == 100` found in `{SOURCE_PATH}`. File unchanged.")

if __name__ == '__main__':
    main()