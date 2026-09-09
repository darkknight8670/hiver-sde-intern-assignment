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
Gemini
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

Observed intent confusions include:

```text
customer_service -> delivery_issue
product_issue     -> return_refund
return_refund     -> order_issue
product_issue     -> order_issue
prime_membership  -> payment_issue
delivery_issue    -> product_issue
promotion_offer   -> other
prime_video       -> other
```

Low-similarity examples also include multilingual scam-related messages, showing a weakness of English-heavy TF-IDF retrieval.

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

### Evaluation limitation

During development, the available Gemini API free-tier request quota was exhausted.

Completed Gemini agent evaluations:

```text
14
```

Completed LLM-as-judge evaluations:

```text
0
```

The 14 successful Gemini evaluations produced:

```text
Intent accuracy: 100.00%
Routing accuracy: 71.43%
```

However, `N=14` is too small to represent the 200-example golden set. These numbers are therefore **preliminary observations only**, not the primary headline result.

No LLM-as-judge score is reported because doing so without completed judgments would be misleading.

## Human Review

Generate the human-review file:

```bash
python -m src.evaluation.create_human_review
```

Output:

```text
data/golden/human_review.jsonl
```

Launch the review interface:

```bash
python -m src.evaluation.review_human
```

The project does not fabricate human-agreement statistics when independent human labels are unavailable.

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

The Gemini agent requires a valid API key:

```bash
python -m src.agent.agent
```

Batch evaluation:

```bash
python -m src.evaluation.run_agent
```

## Headline Result and Its Limitation

The strongest fully evaluated comparison is the 200-example baseline evaluation:

```text
Trivial intent accuracy: 15.50%
Simple intent accuracy:  53.00%

Trivial intent macro-F1: 2.24%
Simple intent macro-F1:  51.81%
```

The retrieval/rule baseline therefore improves intent accuracy by **37.5 percentage points** over the trivial baseline.

### What is misleading about my headline number?

A headline such as **"100% intent accuracy with Gemini"** would be misleading because it is based on only 14 successful evaluations out of the 200-example golden set.

The 200-example baseline comparison is the stronger and more defensible evidence.

## Future Work

If additional development time were available:

1. Complete the 200-example Gemini evaluation.
2. Run LLM-as-judge evaluation on generated responses.
3. Collect independent human ratings for a judge-agreement subset.
4. Improve multilingual retrieval.
5. Replace keyword routing rules with a calibrated routing classifier.
6. Add confidence thresholds and abstention.
7. Add retrieval-quality diagnostics.
8. Evaluate ambiguous and adversarial customer messages.
9. Add automated tests for structured agent output.
10. Integrate live support tooling only after offline evaluation is strong.

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

The key fully evaluated result is:

```text
15.50%  ->  53.00% intent accuracy
```

for the trivial baseline versus the retrieval/rule baseline.

The evaluation also exposes an important weakness: routing requires more than keyword recognition. Cases requiring private account/order investigation should be handled conservatively and escalated when necessary.
