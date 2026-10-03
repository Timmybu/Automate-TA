"""Stage 1: turn raw free-text scheduling constraints into JSON records.

Reads a one-column text/CSV export where each response is one record. Quoted
records may span several lines, as in data/sched_constraints_example.txt, so the
file is read with csv.reader rather than line by line.

No model is called here; this stage only reads and normalizes text.

Usage:
    python tools/jsonify_constraints.py data/sched_constraints_example.txt
    python tools/jsonify_constraints.py input.csv --column 3 --output data/constraints.json
    cat input.txt | python tools/jsonify_constraints.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, TextIO

SCHEMA_VERSION = 1


def read_records(handle: TextIO, column: int = 0, has_header: bool = False) -> list[dict[str, str]]:
    """Return one record per CSV row, preserving newlines inside quoted fields."""

    rows = csv.reader(handle)
    if has_header:
        next(rows, None)

    records: list[dict[str, str]] = []
    for number, row in enumerate(rows, start=1):
        if not row:
            continue
        if column >= len(row):
            raise ValueError(f"Row {number} has {len(row)} column(s); column {column} was requested")
        text = row[column].strip()
        if not text:
            continue
        records.append({"id": f"row-{number}", "text": text})
    return records


def build_payload(records: list[dict[str, str]], source: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "record_count": len(records),
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", nargs="?", type=Path, help="text/CSV file; omit to read stdin")
    parser.add_argument("--column", type=int, default=0, help="0-based column holding the text")
    parser.add_argument("--has-header", action="store_true", help="skip the first row")
    parser.add_argument("--output", type=Path, help="write here instead of stdout")
    args = parser.parse_args(argv)

    if args.input:
        with args.input.open(encoding="utf-8-sig", newline="") as handle:
            records = read_records(handle, args.column, args.has_header)
        source = str(args.input)
    else:
        records = read_records(sys.stdin, args.column, args.has_header)
        source = "<stdin>"

    if not records:
        print("No records found in the input.", file=sys.stderr)
        return 1

    payload = json.dumps(build_payload(records, source), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Wrote {len(records)} records to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
