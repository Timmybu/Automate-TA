"""Extract TA preference survey responses from a CSV export or XLSX workbook into JSON.

This script only reads and normalizes source data. It does not assign numeric values,
map topics to courses, or calculate candidate scores.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, TextIO


DEFAULT_SHEET = "Form Responses 1"
TOP_CHOICE_PREFIX = "Top choices ["
TOPIC_PREFIX = "Topic Areas ["

IDENTITY_HEADERS = {
    "timestamp": "Timestamp",
    "first_name": "First name",
    "last_name": "Last name",
    "email": "Pitt email address",
    "scheduling_constraints": "Scheduling constraints",
    "course_constraints": "Courses constraints",
    "goals": "Goals",
}

NOTES_HEADER_PREFIX = "Anything else we should know?"


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _serializable_timestamp(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return _text(value)


def _extract_bracketed_header(header: str, prefix: str) -> str | None:
    if header.startswith(prefix) and header.endswith("]"):
        return header[len(prefix) : -1].strip()
    return None


def _header_index(headers: list[str], expected: str) -> int:
    try:
        return headers.index(expected)
    except ValueError as exc:
        raise ValueError(f"Required column is missing: {expected!r}") from exc


def _read_workbook_rows(path: Path, sheet_name: str) -> tuple[list[str], list[tuple]]:
    """Return the header row and data rows of a worksheet."""

    from openpyxl import load_workbook  # imported here so .csv input needs no openpyxl

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet_name not in workbook.sheetnames:
            raise ValueError(
                f"Worksheet {sheet_name!r} was not found. "
                f"Available sheets: {', '.join(workbook.sheetnames)}"
            )

        sheet = workbook[sheet_name]
        rows = sheet.iter_rows(values_only=True)
        try:
            raw_headers = next(rows)
        except StopIteration as exc:
            raise ValueError(f"Worksheet {sheet_name!r} is empty") from exc

        return [_text(value) for value in raw_headers], [tuple(row) for row in rows]
    finally:
        workbook.close()


def _read_csv_rows(path: Path) -> tuple[list[str], list[tuple]]:
    """Return the header row and data rows of a CSV export.

    Quoted fields may span several lines, as free-text answers often do, so the
    file is read with csv.reader rather than line by line.
    """

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.reader(handle)
        try:
            raw_headers = next(rows)
        except StopIteration as exc:
            raise ValueError(f"File is empty: {path}") from exc

        return [_text(value) for value in raw_headers], [tuple(row) for row in rows]


def extract_responses(
    source_path: str | Path,
    sheet_name: str = DEFAULT_SHEET,
) -> dict[str, Any]:
    """Return a normalized, JSON-compatible representation of the survey data.

    Accepts a .csv export or an .xlsx workbook; the sheet name applies to
    workbooks only.
    """

    path = Path(source_path)
    if not path.is_file():
        raise FileNotFoundError(f"Response file not found: {path}")

    if path.suffix.lower() == ".csv":
        headers, rows = _read_csv_rows(path)
        source: dict[str, Any] = {"file": str(path)}
        origin = f"File {path.name!r}"
    else:
        headers, rows = _read_workbook_rows(path, sheet_name)
        source = {"workbook": str(path), "sheet": sheet_name}
        origin = f"Worksheet {sheet_name!r}"

    duplicates = sorted({header for header in headers if headers.count(header) > 1})
    if duplicates:
        raise ValueError(f"Duplicate response headers: {', '.join(duplicates)}")

    identity_indexes = {
        field: _header_index(headers, header)
        for field, header in IDENTITY_HEADERS.items()
    }
    timestamp_index = identity_indexes["timestamp"]

    notes_indexes = [
        index
        for index, header in enumerate(headers)
        if header.startswith(NOTES_HEADER_PREFIX)
    ]
    if len(notes_indexes) != 1:
        raise ValueError(
            f"Expected one notes column beginning with {NOTES_HEADER_PREFIX!r}; "
            f"found {len(notes_indexes)}"
        )
    notes_index = notes_indexes[0]

    course_columns: dict[int, str] = {}
    topic_columns: dict[int, str] = {}
    for index, header in enumerate(headers):
        course = _extract_bracketed_header(header, TOP_CHOICE_PREFIX)
        if course is not None:
            course_columns[index] = course
            continue
        topic = _extract_bracketed_header(header, TOPIC_PREFIX)
        if topic is not None:
            topic_columns[index] = topic

    if not course_columns:
        raise ValueError(f"No {TOP_CHOICE_PREFIX!r} columns were found")
    if not topic_columns:
        raise ValueError(f"No {TOPIC_PREFIX!r} columns were found")

    profiles: list[dict[str, Any]] = []
    for raw_row in rows:
        row = list(raw_row) + [None] * (len(headers) - len(raw_row))
        if not _text(row[timestamp_index]):
            continue

        first_name = _text(row[identity_indexes["first_name"]])
        last_name = _text(row[identity_indexes["last_name"]])
        email = _text(row[identity_indexes["email"]])
        name = " ".join(
            part for part in (first_name, last_name) if part
        ).strip()

        profiles.append(
            {
                "candidate_id": email or name,
                "timestamp": _serializable_timestamp(row[timestamp_index]),
                "first_name": first_name,
                "last_name": last_name,
                "name": name,
                "email": email,
                "course_preferences": {
                    course: _text(row[index])
                    for index, course in course_columns.items()
                },
                "topic_ratings": {
                    topic: _text(row[index])
                    for index, topic in topic_columns.items()
                },
                "scheduling_constraints": _text(
                    row[identity_indexes["scheduling_constraints"]]
                ),
                "course_constraints": _text(
                    row[identity_indexes["course_constraints"]]
                ),
                "goals": _text(row[identity_indexes["goals"]]),
                "notes": _text(row[notes_index]),
            }
        )

    if not profiles:
        raise ValueError(f"{origin} contains no response rows")

    return {
        "schema_version": 1,
        "source": source,
        "courses": list(course_columns.values()),
        "topics": list(topic_columns.values()),
        "profile_count": len(profiles),
        "profiles": profiles,
    }


def extract_workbook(
    workbook_path: str | Path,
    sheet_name: str = DEFAULT_SHEET,
) -> dict[str, Any]:
    """Workbook-only alias kept for existing callers."""

    return extract_responses(workbook_path, sheet_name)


def write_json(payload: dict[str, Any], destination: TextIO) -> None:
    json.dump(payload, destination, indent=2, ensure_ascii=False)
    destination.write("\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract and normalize TA preference survey responses."
    )
    parser.add_argument(
        "responses", type=Path, help="TA preference responses as .csv or .xlsx"
    )
    parser.add_argument("--sheet", default=DEFAULT_SHEET, help="worksheet name (.xlsx only)")
    parser.add_argument("--output", type=Path, help="Output JSON path; defaults to stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = extract_responses(args.responses, args.sheet)

    destination: TextIO
    close_destination = False
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        destination = args.output.open("w", encoding="utf-8")
        close_destination = True
    else:
        destination = sys.stdout

    try:
        write_json(payload, destination)
    finally:
        if close_destination:
            destination.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
