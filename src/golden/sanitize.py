"""Remove post-message turns from an existing golden set."""

import json
from pathlib import Path


GOLDEN_FILE = Path("data/golden/golden_set.jsonl")


def safe_context(context):
    """Keep only turns before the evaluated customer message."""
    prefix = []

    for turn in context or []:
        if turn.get("speaker") == "customer":
            break
        prefix.append(turn)

    return prefix


def sanitize(path=GOLDEN_FILE):
    path = Path(path)
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    for record in records:
        record["context"] = safe_context(record.get("context", []))

    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Sanitized {len(records)} golden records: {path}")


if __name__ == "__main__":
    sanitize()