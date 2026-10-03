"""Stage 2: convert jsonified free-text constraints into weekly schedule rules.

Reads the profiles JSON produced by stage 1
(scripts/ta_preferences/extract_ta_preferences.py), sends each response's
scheduling_constraints text to an Azure OpenAI deployment under a strict JSON
schema, and writes weekly rules keyed by candidate_id. Only the constraint text
is sent; names and emails stay local.

Only recurring weekly availability is extracted. One-off dates, conditional
plans, and anything else that is not a weekly rule are ignored by design.

Usage:
    python scripts/ta_preferences/extract_ta_preferences.py data/real_export.csv | python tools/parse_constraints.py --output data/weekly_constraints.json
    python tools/parse_constraints.py data/ta_profiles.json --output data/weekly_constraints.json

Also accepts the simpler {"records": [{"id", "text"}]} shape from
tools/jsonify_constraints.py for constraint-only test fixtures.

Progress goes to stderr, so stdout stays pipeable JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = 1

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
TIME = {"type": ["string", "null"], "description": "24-hour HH:MM, or null for open-ended"}

# Strict mode: every property must be required and additionalProperties false;
# optional values are expressed as nullable instead of omitted.
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["rules", "interpretation"],
    "properties": {
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "days", "start", "end"],
                "properties": {
                    "kind": {"type": "string", "enum": ["unavailable", "available_only", "prefer_not"]},
                    "days": {"type": "array", "items": {"type": "string", "enum": DAYS}},
                    "start": TIME,
                    "end": TIME,
                },
            },
        },
        "interpretation": {"type": "string"},
    },
}

SYSTEM = """You convert a teaching assistant's free-text scheduling constraint into weekly rules.

Rule kinds:
- unavailable: the TA cannot work in this window.
- available_only: the TA can work ONLY in these windows; all other times are unavailable.

Conventions:
- Days are MON..SUN. An empty days list means the rule applies to every day.
- Times are 24-hour HH:MM. start null = start of day, end null = end of day.
- "Morning" = before 12:00. "Afternoon" = 12:00-17:00. "Evening" = after 17:00.
- A response that lists class times, meetings, or other commitments describes
  times the TA is busy, so use unavailable.
- A response that lists working hours or free times describes availability, so
  use available_only.
- No constraints stated ("None", "N/A", "NA", "TBD", blank, "flexible") -> empty rules.

Extract only recurring weekly availability. Ignore specific calendar dates,
conference travel, conditional or possible future enrollment, and any other
detail that does not repeat weekly. Never invent a rule that is not stated.

interpretation is one plain-English sentence stating exactly what the rules
mean, so a person can check them.

Examples:
"No Friday" -> [{"kind":"unavailable","days":["FRI"],"start":null,"end":null}]
"Mon/Wed only" -> [{"kind":"available_only","days":["MON","WED"],"start":null,"end":null}]
"No mornings" -> [{"kind":"unavailable","days":[],"start":null,"end":"12:00"}]
"Fri 12:30-1:30 CS 2003" -> [{"kind":"unavailable","days":["FRI"],"start":"12:30","end":"13:30"}]"""

HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def make_client() -> OpenAI:
    load_dotenv(ROOT / ".env")
    missing = [key for key in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY") if not os.getenv(key)]
    if missing:
        sys.exit(f"Missing {', '.join(missing)} in .env (see .env.example).")
    return OpenAI(
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/",
        api_key=os.environ["AZURE_OPENAI_KEY"],
    )


def load_entries(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Accept stage 1 records or extract_ta_preferences.py profiles."""

    if "records" in payload:
        return [{"id": r["id"], "text": r["text"]} for r in payload["records"]]
    if "profiles" in payload:
        return [
            {"id": p["candidate_id"], "text": p.get("scheduling_constraints", "")}
            for p in payload["profiles"]
        ]
    raise ValueError("Input JSON has neither 'records' (stage 1) nor 'profiles' keys")


def check_times(entry_id: str, rules: list[dict[str, Any]]) -> None:
    """Warn about malformed times; the schema cannot express the HH:MM format."""

    for rule in rules:
        for key in ("start", "end"):
            if rule[key] is not None and not HHMM.match(rule[key]):
                print(f"  warning: {entry_id} has a bad {key} time: {rule[key]!r}", file=sys.stderr)


def parse(client: OpenAI, deployment: str, text: str) -> dict[str, Any]:
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "weekly_constraint", "strict": True, "schema": SCHEMA},
        },
        # GPT-5 models reject temperature; keep reasoning light for a simple extraction.
        reasoning_effort="low",
    )
    message = response.choices[0].message
    if message.refusal:
        raise RuntimeError(f"Model refused: {message.refusal}")
    return json.loads(message.content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", nargs="?", type=Path, help="stage 1 JSON; omit to read stdin")
    parser.add_argument("--output", type=Path, help="write here instead of stdout")
    parser.add_argument("--limit", type=int, help="only process the first N entries")
    args = parser.parse_args(argv)

    raw = args.input.read_text(encoding="utf-8-sig") if args.input else sys.stdin.read()
    # Piping between programs in Windows PowerShell prepends a BOM.
    entries = load_entries(json.loads(raw.lstrip("﻿")))
    if args.limit:
        entries = entries[: args.limit]

    client = make_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "constraint-parser")

    results: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        print(f"[{index}/{len(entries)}] {entry['id']}", file=sys.stderr)
        parsed = parse(client, deployment, entry["text"])
        check_times(entry["id"], parsed["rules"])
        results.append({**entry, **parsed})

    payload = {
        "schema_version": SCHEMA_VERSION,
        "deployment": deployment,
        "entry_count": len(results),
        "entries": results,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {len(results)} entries to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
