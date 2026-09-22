"""Convert free-text TA scheduling constraints into structured rules.

Calls an Azure OpenAI deployment with a strict JSON schema and caches the
results in data/parsed_constraints.json, keyed by the original text, so each
distinct constraint is only sent to Azure once.

Usage:
    python tools/parse_constraints.py                     # parse the sample constraints
    python tools/parse_constraints.py "No Friday" "..."   # parse specific strings
    python tools/parse_constraints.py --file input.txt    # one constraint per line
    python tools/parse_constraints.py --force             # ignore the cache
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "parsed_constraints.json"

# Constraints from the sample TA data in assets/app.js.
SAMPLES = ["Tue after 4 PM", "None", "No Friday", "Mon/Wed only", "After 11 AM", "No mornings"]

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
TIME = {"type": ["string", "null"], "description": "24-hour HH:MM, or null for open-ended"}

# Strict mode: every property must be required and additionalProperties false;
# optional values are expressed as nullable instead of omitted.
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["rules", "ambiguous", "interpretation"],
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
        "ambiguous": {"type": "boolean"},
        "interpretation": {"type": "string"},
    },
}

SYSTEM = """You convert a teaching assistant's free-text scheduling constraint into rules.

Rule kinds:
- unavailable: the TA cannot work in this window.
- available_only: the TA can work ONLY in these windows (all other times are unavailable).
- prefer_not: the TA would rather not work in this window but could if needed.

Conventions:
- Days are MON..SUN. An empty days list means the rule applies every day.
- Times are 24-hour HH:MM. start null = start of day, end null = end of day.
- "Morning" = before 12:00. "Afternoon" = 12:00-17:00. "Evening" = after 17:00.
- "None", blank, or "no constraints" -> rules is an empty list.

If the text could reasonably mean two different things, choose the most likely
reading AND set ambiguous to true. interpretation is one plain-English sentence
stating exactly what the rules mean, so a person can verify it.

Examples:
"No Friday" -> [{"kind":"unavailable","days":["FRI"],"start":null,"end":null}]
"Mon/Wed only" -> [{"kind":"available_only","days":["MON","WED"],"start":null,"end":null}]
"No mornings" -> [{"kind":"unavailable","days":[],"start":null,"end":"12:00"}]"""

HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def make_client() -> OpenAI:
    load_dotenv(ROOT / ".env")
    missing = [k for k in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY") if not os.getenv(k)]
    if missing:
        sys.exit(f"Missing {', '.join(missing)} in .env (see example.env).")
    return OpenAI(
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1/",
        api_key=os.environ["AZURE_OPENAI_KEY"],
    )


def validate(result: dict) -> dict:
    """Catch malformed times the schema can't express; flag them for review."""
    for rule in result["rules"]:
        for key in ("start", "end"):
            if rule[key] is not None and not HHMM.match(rule[key]):
                result["ambiguous"] = True
                result["interpretation"] += f" [bad {key} time: {rule[key]!r}]"
    return result


def parse(client: OpenAI, deployment: str, text: str) -> dict:
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "constraint", "strict": True, "schema": SCHEMA},
        },
        # GPT-5 models reject temperature; keep reasoning light for a simple extraction.
        reasoning_effort="low",
    )
    message = response.choices[0].message
    if message.refusal:
        raise RuntimeError(f"Model refused: {message.refusal}")
    return validate(json.loads(message.content))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("texts", nargs="*", help="constraint strings to parse")
    parser.add_argument("--file", type=Path, help="text file with one constraint per line")
    parser.add_argument("--force", action="store_true", help="re-parse even if cached")
    args = parser.parse_args()

    texts = list(args.texts)
    if args.file:
        texts += [line.strip() for line in args.file.read_text(encoding="utf-8").splitlines() if line.strip()]
    texts = list(dict.fromkeys(texts or SAMPLES))  # dedupe, keep order

    cache = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    client = make_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "constraint-parser")

    for text in texts:
        if text in cache and not args.force:
            status = "cached"
        else:
            cache[text] = parse(client, deployment, text)
            status = "parsed"
        result = cache[text]
        flag = "  [REVIEW]" if result["ambiguous"] else ""
        print(f"{status:>6}  {text!r} -> {result['interpretation']}{flag}")

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {len(cache)} entries to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
