"""
Clean houses_train.jsonl
- Remove entries with sold == 'no'
- Remove entries with missing or empty 'year'
- Replace rooms == "" with "0 rooms"

Usage (default paths):
    python scripts/clean_houses.py
Or specify input/output:
    python scripts/clean_houses.py --input data/houses_train.jsonl --output data/houses_train_cleaned.jsonl
"""
from pathlib import Path
import json
import argparse


def clean_file(input_path: Path, output_path: Path):
    total = 0
    removed_sold_no = 0
    removed_missing_year = 0
    rooms_fixed = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open('r', encoding='utf-8') as inf, output_path.open('w', encoding='utf-8') as outf:
        for raw in inf:
            raw = raw.strip()
            if not raw:
                continue
            total += 1
            try:
                rec = json.loads(raw)
            except Exception:
                # skip malformed lines
                continue

            # remove if sold == 'no' (case-insensitive)
            sold_val = rec.get('sold')
            if isinstance(sold_val, str) and sold_val.strip().lower() == 'no':
                removed_sold_no += 1
                continue

            # remove if year is missing or empty (None or empty string)
            if 'year' not in rec or rec.get('year') in (None, ""):
                removed_missing_year += 1
                continue

            # fix rooms field if empty string
            if rec.get('rooms') == "":
                rec['rooms'] = "0 rooms"
                rooms_fixed += 1

            outf.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return {
        'total_seen': total,
        'removed_sold_no': removed_sold_no,
        'removed_missing_year': removed_missing_year,
        'rooms_fixed': rooms_fixed,
        'kept': total - removed_sold_no - removed_missing_year,
        'output_path': str(output_path)
    }


if __name__ == '__main__':
    # compute script-relative sensible defaults so running the script from any cwd works
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent  # knutKnutOppgave
    default_input = project_dir / 'data' / 'houses_train.jsonl'
    default_output = project_dir / 'data' / 'houses_train_cleaned.jsonl'

    parser = argparse.ArgumentParser(description='Clean houses JSONL file')
    parser.add_argument('--input', '-i', type=str, default=str(default_input),
                        help='Path to input JSONL file (default: data/houses_train.jsonl relative to the script)')
    parser.add_argument('--output', '-o', type=str, default=str(default_output),
                        help='Path to write cleaned JSONL (default: data/houses_train_cleaned.jsonl relative to the script)')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # If the provided input doesn't exist, try interpreting it relative to the project data folder
    if not input_path.exists():
        alt = project_dir / args.input
        if alt.exists():
            input_path = alt
        else:
            print(f"Input file does not exist: {args.input}")
            raise SystemExit(1)

    stats = clean_file(input_path, output_path)

    print('Cleaning complete:')
    print(f"  total records read: {stats['total_seen']}")
    print(f"  removed (sold == 'no'): {stats['removed_sold_no']}")
    print(f"  removed (missing/empty year): {stats['removed_missing_year']}")
    print(f"  rooms fixed (\"\" -> '0 rooms'): {stats['rooms_fixed']}")
    print(f"  records kept: {stats['kept']}")
    print(f"  cleaned file: {stats['output_path']}")
