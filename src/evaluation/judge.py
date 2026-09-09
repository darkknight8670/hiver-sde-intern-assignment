import json
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = PROJECT_ROOT / "src" / "agent"
sys.path.insert(0, str(AGENT_DIR))

from provider import LLMProvider
GOLDEN_FILE = PROJECT_ROOT / "data/golden/golden_set.jsonl"
AGENT_FILE = PROJECT_ROOT / "results/evaluation/agent_predictions.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "results/evaluation/llm_judge.jsonl"


JUDGE_SYSTEM_PROMPT = """
You are evaluating an AI customer-support response for AmazonHelp.

Your job is to judge the QUALITY of the AI-generated response.

Use only the information provided in the evaluation record:
- customer message
- conversation context
- historically retrieved AmazonHelp responses
- AI response

Do NOT judge whether the predicted intent label matches the gold label.
Do NOT invent Amazon policies or facts that are not supported by the evidence.

Score each criterion from 1 to 5.

Criteria:

1. groundedness
5 = strongly grounded in the provided historical evidence/context
4 = mostly grounded, with minor unsupported phrasing
3 = partially grounded
2 = contains significant unsupported claims
1 = largely fabricated or unrelated

2. helpfulness
5 = directly addresses the customer's issue and gives a useful next step
4 = useful but could be more specific
3 = somewhat useful
2 = vague or only partially addresses the issue
1 = does not meaningfully help

3. correctness
5 = accurate and appropriate given the available evidence
4 = mostly correct with a minor issue
3 = uncertain or partially correct
2 = contains a significant likely error
1 = clearly incorrect

4. tone
5 = professional, empathetic, concise, and appropriate
4 = good tone with minor issues
3 = acceptable
2 = awkward or noticeably inappropriate
1 = clearly inappropriate

5. hallucination
This score measures absence of unsupported claims.
5 = no meaningful hallucination
4 = very minor unsupported detail
3 = some questionable unsupported detail
2 = significant unsupported claims
1 = severe fabrication

Then provide:
- overall: 1 to 5
- acceptable: true or false
- reason: concise explanation of the main strengths/weaknesses

Return ONLY valid JSON in exactly this structure:

{
  "groundedness": 1,
  "helpfulness": 1,
  "correctness": 1,
  "tone": 1,
  "hallucination": 1,
  "overall": 1,
  "acceptable": true,
  "reason": "..."
}
"""


def load_jsonl(path):
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def load_existing():
    if not OUTPUT_FILE.exists():
        return {}

    records = load_jsonl(OUTPUT_FILE)

    return {
        record["example_id"]: record
        for record in records
        if (
            record.get("status") == "success"
            and not record.get("mock")
            and not record.get("mock_disclaimer")
            and record.get("example_id")
        )
    }


def remove_synthetic_records():
    if not OUTPUT_FILE.exists():
        return

    records = load_jsonl(OUTPUT_FILE)
    genuine = [
        record
        for record in records
        if (
            record.get("status") == "success"
            and not record.get("mock")
            and not record.get("mock_disclaimer")
        )
    ]

    if len(genuine) != len(records):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for record in genuine:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_prompt(gold, prediction):
    context = gold.get("context", [])
    retrieved = prediction.get("retrieved_examples", [])

    return f"""
Evaluate this AmazonHelp support response.

CUSTOMER MESSAGE:
{gold["customer_message"]}

CONVERSATION CONTEXT:
{json.dumps(context, ensure_ascii=False, indent=2)}

HISTORICAL AMAZONHELP RESPONSES:
{json.dumps(retrieved, ensure_ascii=False, indent=2)}

AI-GENERATED RESPONSE:
{prediction["response"]}

Evaluate the AI response using the rubric.
Return ONLY the required JSON.
"""


def parse_json(text):
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return json.loads(text)


def validate_result(result):
    required = [
        "groundedness",
        "helpfulness",
        "correctness",
        "tone",
        "hallucination",
        "overall",
        "acceptable",
        "reason",
    ]

    for field in required:
        if field not in result:
            raise ValueError(f"Missing judge field: {field}")

    for field in [
        "groundedness",
        "helpfulness",
        "correctness",
        "tone",
        "hallucination",
        "overall",
    ]:
        value = result[field]

        if not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(
                f"{field} must be an integer from 1 to 5, got {value}"
            )

    if not isinstance(result["acceptable"], bool):
        raise ValueError("acceptable must be boolean")

    return result


def append_record(record):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    remove_synthetic_records()
    provider = LLMProvider()

    gold_records = load_jsonl(GOLDEN_FILE)

    agent_records = load_jsonl(AGENT_FILE)

    agent_success = {
        record["example_id"]: record
        for record in agent_records
        if record.get("status") == "success"
    }

    already_judged = load_existing()

    pending = [
        example_id
        for example_id in agent_success
        if example_id not in already_judged
    ]

    print("=" * 82)
    print("LLM-AS-JUDGE")
    print("=" * 82)
    print()
    print(f"Golden examples:       {len(gold_records)}")
    print(f"Successful agent predictions: {len(agent_success)}")
    print(f"Already judged:        {len(already_judged)}")
    print(f"Remaining to judge:    {len(pending)}")
    print()

    if not pending:
        print("Nothing new to judge.")
        return

    gold_by_id = {
        record["example_id"]: record
        for record in gold_records
    }

    success_count = 0
    failure_count = 0

    for position, example_id in enumerate(pending, start=1):

        print(f"[{position}/{len(pending)}] {example_id}")

        gold = gold_by_id.get(example_id)
        prediction = agent_success[example_id]

        if gold is None:
            print("ERROR: gold example not found")
            failure_count += 1
            continue

        prompt = build_prompt(gold, prediction)

        try:
            raw_output = provider.generate(
                JUDGE_SYSTEM_PROMPT,
                prompt,
            ).strip()

            if not raw_output:
                raise RuntimeError("Empty judge response")

            result = validate_result(parse_json(raw_output))

            record = {
                "example_id": example_id,
                "provider": provider.provider,
                "model": provider.model,
                "groundedness": result["groundedness"],
                "helpfulness": result["helpfulness"],
                "correctness": result["correctness"],
                "tone": result["tone"],
                "hallucination": result["hallucination"],
                "overall": result["overall"],
                "acceptable": result["acceptable"],
                "reason": result["reason"],
                "status": "success",
            }

            append_record(record)

            success_count += 1

            print(
                f"  overall={result['overall']} "
                f"acceptable={result['acceptable']}"
            )

        except Exception as e:

            error_message = str(e)

            print(f"  ERROR: {error_message}")

            failure_count += 1

            # Stop immediately on quota/rate-limit errors.
            if "429" in error_message or "quota" in error_message.lower():
                print()
                print("Provider quota/rate limit detected.")
                print("Stopping this run so the script can resume later.")
                break

    judged_total = len(already_judged) + success_count

    print()
    print("=" * 82)
    print("JUDGE SUMMARY")
    print("=" * 82)
    print(f"Successful judgments this run: {success_count}")
    print(f"Failures this run:             {failure_count}")
    print(f"Total successful judgments:    {judged_total}")
    print(f"Remaining:                     {len(agent_success) - judged_total}")
    print()
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()