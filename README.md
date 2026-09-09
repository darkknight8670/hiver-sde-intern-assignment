# AI Support Agent for AmazonHelp

An AI customer-support agent built for the Hiver SDE Intern take-home assignment using the Customer Support on Twitter (TWCS) dataset.

The system:
- selects a support-heavy brand
- reconstructs customer-support episodes
- defines a compact intent taxonomy
- retrieves historically similar support interactions
- classifies incoming messages
- decides auto-handle vs human escalation
- drafts grounded responses
- evaluates against simple baselines

Selected brand: **AmazonHelp**

## Project Structure

```text
Hiver_assignment/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── golden/
│   ├── processed/
│   └── raw/
├── results/
│   ├── brand_selection/
│   ├── data_profile/
│   ├── intent_analysis/
│   ├── intent_discovery/
│   ├── baselines/
│   ├── evaluation/
│   ├── intent_taxonomy.json
│   └── decision_log.md
└── src/
    ├── agent/
    ├── baselines/
    ├── brand/
    ├── data/
    ├── evaluation/
    ├── golden/
    └── intent/
```

## Requirements

Recommended Python version: **Python 3.10+**

Install dependencies:

```bash
pip install -r requirements.txt
```

Main dependencies:

```text
pandas
numpy
scikit-learn
python-dotenv
tqdm
kaggle
PyPDF2
pytest
google-genai
groq
```

## Dataset

This project uses the **Customer Support on Twitter (TWCS)** dataset.

Expected location:

```text
data/raw/twcs/twcs.csv
```

The dataset contains customer-support tweets, support responses, timestamps, inbound/outbound indicators, and reply relationships.

## Environment Setup

Create `.env` in the project root:

```text
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

# Gemini remains available as an alternative provider.
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash
```

Do not commit `.env`.

## Data Pipeline

### Profile dataset

```bash
python -m src.data.profile
```

Outputs are written to:

```text
results/data_profile/
```

### Select brand

```bash
python -m src.brand.select
```

Selected brand:

```text
AmazonHelp
```

Outputs:

```text
results/brand_selection/
```

### Reconstruct support episodes

```bash
python -m src.data.conversations
```

Output:

```text
data/processed/amazonhelp_episodes.jsonl
```

The final reconstruction uses local reply chains centered on customer messages directly answered by AmazonHelp. This avoids the unrelated, excessively long threads produced by the initial root-thread approach.

### Create splits

```bash
python -m src.data.split
```

Approximate split:

```text
70% train
15% validation
15% test
```

Files:

```text
data/processed/splits/train.jsonl
data/processed/splits/validation.jsonl
data/processed/splits/test.jsonl
data/processed/splits/split_summary.json
```

The split has zero tweet overlap across train, validation, and test.

## Intent Taxonomy

The final taxonomy contains 12 intents:

```text
delivery_issue
order_issue
return_refund
payment_issue
account_access
product_issue
prime_video
seller_marketplace
promotion_offer
prime_membership
customer_service
other
```

Run intent analysis:

```bash
python -m src.intent.analyze
```

Taxonomy:

```text
results/intent_taxonomy.json
```

The project also experimented with TF-IDF + K-Means clustering. The resulting clusters were highly imbalanced, so they were not used as the final taxonomy.

## Golden Set

A fixed 200-example golden set is stored at:

```text
data/golden/golden_set.jsonl
```

It is sampled from the held-out test split and contains intent and routing annotations plus rationale and sampling metadata.

Inspect it:

```bash
python -m src.golden.inspect
```

Guidelines:

```text
data/golden/annotation_guidelines.md
```

## Baseline 1: Trivial

The trivial baseline:
- predicts the majority intent
- always escalates to a human
- uses the most common historical response

Run:

```bash
python -m src.baselines.trivial
```

Output:

```text
results/baselines/trivial_predictions.jsonl
```

## Baseline 2: Retrieval + Rules

The second baseline combines:
- TF-IDF retrieval
- keyword-based intent rules
- deterministic routing rules

Run:

```bash
python -m src.baselines.simple
```

Output:

```text
results/baselines/simple_predictions.jsonl
```

## Final AI Agent

The final system uses retrieval-augmented generation:

```text
Customer Message
       |
       v
TF-IDF Historical Retrieval
       |
       v
Top Similar AmazonHelp Interactions
       |
        v
Groq / Gemini
       |
       +----------------+
       |        |       |
       v        v       v
    Intent   Routing  Response
```

The agent is instructed to:
- ground responses in historical examples
- avoid inventing policies
- avoid unsupported refund/delivery guarantees
- avoid claiming account access
- escalate account/order-specific investigations
- return structured JSON

Output schema:

```json
{
  "intent": "delivery_issue",
  "routing": "human_escalation",
  "routing_reason": "The issue requires order-specific investigation.",
  "response": "..."
}
```

Run interactively:

```bash
python -m src.agent.agent
```

Example:

```text
Customer: My package says delivered but I never received it
```

## Batch Agent Evaluation

Run:

```bash
python -m src.evaluation.run_agent
```

Successful predictions:

```text
results/evaluation/agent_predictions.jsonl
```

The evaluator is resumable. Failed API calls are not treated as completed evaluations.

## Evaluation Metrics

Run:

```bash
python -m src.evaluation.metrics
```

Metrics:
- intent accuracy
- intent macro-F1
- intent weighted-F1
- routing accuracy
- routing macro-F1
- routing weighted-F1

Output:

```text
results/evaluation/evaluation_summary.json
```

## Baseline Comparison

Run:

```bash
python -m src.evaluation.compare
```

The comparison joins predictions to the golden set using `example_id`.

Current fully evaluated 200-example results:

| System | N | Intent Accuracy | Intent Macro-F1 | Routing Accuracy | Routing Macro-F1 |
|---|---:|---:|---:|---:|---:|
| Trivial | 200 | 15.50% | 2.24% | 72.00% | 41.86% |
| Simple | 200 | 53.00% | 51.81% | 35.00% | 32.00% |
| Final Groq agent | 200 | 71.50% | 68.66% | 85.50% | 83.54% |

The final Groq agent's weighted F1 scores are 71.43% for intent and 86.04% for routing. All three systems use the same 200-example golden-set denominator.

The simple baseline improves intent accuracy by **37.5 percentage points** over the trivial baseline.

## Routing Findings

The simple baseline has:

```text
Routing accuracy: 35.00%
Routing macro-F1: 32.00%
Routing errors: 130
False negatives: 130
False positives: 0
```

It is therefore too willing to auto-handle cases that should be escalated.

Common problematic cases include:
- missing packages
- delivered-but-not-received packages
- wrong delivery locations
- damaged products
- wrong products
- pre-order delivery problems
- account/order-specific investigations

## Error Analysis

Run:

```bash
python -m src.evaluation.error_analysis
```

Output:

```text
results/evaluation/error_analysis.json
```

The final agent artifact contains 57 intent errors and 29 routing errors. Its largest observed intent confusions include:

```text
return_refund     -> product_issue (4)
prime_membership  -> payment_issue (3)
promotion_offer   -> other (3)
customer_service  -> delivery_issue (3)
customer_service  -> product_issue (2)
delivery_issue    -> customer_service (2)
```

Routing errors contain 24 false negatives, where the agent auto-handled a case that was labelled for escalation, and 5 false positives. Representative risks are refunds, seller disputes, complaints after previous support, account/security issues, and order-specific investigations. The full examples are stored in `results/evaluation/error_analysis.json`.

## LLM-as-Judge

The project includes an LLM-as-judge harness:

```bash
python -m src.evaluation.judge
```

It evaluates:
- groundedness
- helpfulness
- correctness
- tone
- hallucination
- overall quality
- acceptability

Output:

```text
results/evaluation/llm_judge.jsonl
```

The harness is resumable.

### Final evaluation status

During development, the available Gemini API quota interrupted the initial batch. Groq was subsequently used to complete the final agent evaluation.

```text
Agent predictions:       200 / 200
Genuine LLM-judge rows:  200 / 200
```

The Groq judge results are model-generated quality assessments, not human evaluation.

The genuine Groq judge used provider `Groq` and model `openai/gpt-oss-120b`. Its mean overall score was 4.64/5, median 5/5, and acceptable rate 96.0%. These are automated judge results, not human evaluation.

## What is misleading about my headline number?

The 200-example score is useful but is not a universal measure of production quality. The golden set is a fixed sample from a random episode-level split, and results depend on the selected Groq model, prompt, historical-example retrieval, and provider behavior. API/provider differences can change outputs. The LLM judge is an automated rubric-based evaluator and may be biased or inconsistent. Baseline and agent metrics use the same 200-example denominator; judge metrics describe response quality separately rather than classification accuracy.

## Report

The concise submission report, including evaluation methodology, top failure examples, next steps, and limitations, is available in [REPORT.md](REPORT.md).

## Reproduction Notes

The committed golden set, baseline predictions, final agent predictions, judge records, and aggregate JSON files reproduce the reported metrics without API access. Re-running the final agent or judge requires a provider API key and the corresponding model. The original TWCS CSV and generated processed JSONL splits are intentionally excluded because they are large; the committed final predictions contain populated historical AmazonHelp retrieval examples with similarity scores. To rebuild the retrieval corpus or independently rerun the agent evaluation, obtain TWCS and run the data pipeline first.

## Decision Log

Major design decisions are documented in:

```text
results/decision_log.md
```

Important decisions include:
- selecting AmazonHelp
- local support episode reconstruction
- episode-level splitting
- rejecting naive TF-IDF clustering
- defining a 12-intent taxonomy
- creating a fixed golden set
- trivial and retrieval/rule baselines
- historical retrieval for grounding
- conservative escalation
- structured JSON output
- explicit handling of API quota limitations

## What the System Does Not Build

This is an offline evaluation prototype. It does not include:
- live Twitter integration
- live Amazon account access
- real order lookup
- real refund processing
- production authentication
- production human-agent dashboards
- persistent customer memory
- real-time policy verification
- production monitoring
- production deployment infrastructure

A production system would require these capabilities plus additional security, privacy, safety, and reliability controls.

## Reproducibility

Major generated artifacts are stored under:

```text
results/
```

Main reproducible commands:

```bash
python -m src.data.profile
python -m src.brand.select
python -m src.data.conversations
python -m src.data.split
python -m src.intent.analyze

python -m src.baselines.trivial
python -m src.baselines.simple

python -m src.evaluation.evaluate
python -m src.evaluation.compare
python -m src.evaluation.error_analysis
```

The final agent requires a valid provider API key. Configure `LLM_PROVIDER=groq`, `GROQ_API_KEY`, and `GROQ_MODEL` in `.env` for the committed final provider, or configure the Gemini variables for the alternative provider:

```bash
python -m src.agent.agent
```

Batch evaluation:

```bash
python -m src.evaluation.run_agent
```

## Final Headline Result and Its Limitation

The final 200-example comparison is:

```text
Trivial intent accuracy:      15.50%
Simple intent accuracy:       53.00%
Final Groq agent accuracy:    71.50%
Final Groq agent macro-F1:    68.66%
Final Groq routing accuracy:  85.50%
```

The final agent was evaluated on all 200 examples. The Groq judge evaluated 200 real agent responses.

### What is misleading about my headline number?

The 71.5% intent accuracy and 85.5% routing accuracy are measured on a 200-example set sampled from a held-out test split rather than representing the full TWCS distribution. The final agent uses historical-example retrieval followed by LLM generation, and the result depends on the selected Groq model, prompt, provider behavior, and taxonomy. The automated LLM judge is an additional quality signal, not a production guarantee. These results demonstrate a promising prototype rather than production-level accuracy.

## Future Work

If additional development time were available:

1. Restore the full generated AmazonHelp training split and rerun retrieval-backed evaluation.
2. Improve multilingual and security-message retrieval.
3. Replace keyword routing rules with a calibrated routing classifier.
4. Add confidence thresholds and abstention.
5. Add retrieval-quality diagnostics and regression tests for observed confusions.
6. Evaluate multiple providers under the same prompt and denominator.
7. Integrate live support tooling only after offline evaluation is strong.

## Summary

The final prototype combines:

```text
Historical Support Data
        +
Episode Reconstruction
        +
Compact Intent Taxonomy
        +
Historical Retrieval
        +
LLM Reasoning
        +
Explicit Escalation Policy
        +
Automated Evaluation
```

The key final result is:

```text
15.50%  ->  53.00%  ->  71.50% intent accuracy
```

for the trivial baseline, retrieval/rule baseline, and final Groq agent.

The evaluation also exposes an important weakness: routing requires more than keyword recognition. Cases requiring private account/order investigation should be handled conservatively and escalated when necessary.
