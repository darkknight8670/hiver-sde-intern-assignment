# Hiver SDE Intern Assignment Report

## 1. Problem Framing

This project builds an offline AmazonHelp customer-support assistant. Given a customer message and optional context, it predicts one of 12 support intents, chooses `auto_handle` or `human_escalation`, and drafts a concise response grounded in historical support behavior.

The goal is not to claim production automation. It is to compare a structured retrieval/rules baseline with a retrieval-augmented language-model agent under a fixed evaluation protocol.

## 2. Dataset and Episode Construction

The source is Customer Support on Twitter (TWCS). AmazonHelp was selected because it has broad support coverage across delivery, orders, payments, accounts, products, Prime, and marketplace issues. Conversations were reconstructed as local customer-to-AmazonHelp support episodes. A root-thread approach was rejected because it produced long threads containing unrelated cases.

The data split is random and episode-level: 70% train, 15% validation, and 15% test. Tweet overlap across splits is zero, although customer-account overlap is possible because some reply chains involve multiple customer accounts. The golden set contains 200 examples sampled from the held-out test split.

Intent and routing annotations were prepared using the project's annotation workflow; independent human validation of these annotations was not completed.

## 3. Intent Taxonomy

The fixed taxonomy has 12 intents:

`delivery_issue`, `order_issue`, `return_refund`, `payment_issue`, `account_access`, `product_issue`, `prime_video`, `seller_marketplace`, `promotion_offer`, `prime_membership`, `customer_service`, and `other`.

## 4. Agent Architecture

The intended architecture is:

1. Retrieve similar historical AmazonHelp customer/support pairs with TF-IDF.
2. Include retrieved evidence and only context that precedes the incoming
   customer message in the prompt.
3. Ask the selected LLM to classify intent, select routing, and draft a response.
4. Parse and validate a fixed JSON schema.

The final provider is configured through the shared provider adapter. Groq
using `openai/gpt-oss-120b` is the intended final configuration, and Gemini
remains supported as an alternative provider. The repaired evaluation protocol
is versioned as `answer-leakage-fixed-v2`.

## 5. What I Did Not Build

This is not a production support system. It does not provide live Twitter integration, Amazon account or order access, real refunds, production authentication, persistent customer memory, real-time policy verification, agent dashboards, monitoring, or deployment infrastructure.

## 6. Evaluation Design

The fixed 200-example golden set is joined by `example_id`. All baseline and agent classification metrics use the same denominator. Failed API calls are excluded rather than fabricated. The final agent has 200 successful unique predictions. The LLM judge evaluates only real agent predictions and does not use the gold intent to score response quality.

## 7. Baselines

The trivial baseline predicts the majority intent and always escalates. The retrieval-plus-rules baseline uses TF-IDF retrieval and deterministic keyword/routing rules. The final agent uses the provider-backed structured LLM path.

## 8. Evaluation Repair

The original evaluation exposed the target historical support response in
context. The golden set has been sanitized so only turns before the evaluated
customer message can be passed to the model. Legacy predictions are excluded
using evaluation version `answer-leakage-fixed-v2`.

## 9. Final Results

| System | N | Intent accuracy | Intent macro-F1 | Intent weighted-F1 | Routing accuracy | Routing macro-F1 | Routing weighted-F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Trivial | 200 | 15.50% | 2.24% | 4.16% | 72.00% | 41.86% | 60.28% |
| Retrieval + rules | 200 | 53.00% | 51.81% | 53.33% | 35.00% | 32.00% | 25.72% |
| Repaired Groq agent | 200 | **73.00%** | **68.53%** | **72.34%** | **76.00%** | **74.26%** | **77.20%** |

The repaired Groq agent improves intent accuracy by 20.00 percentage points
over the retrieval-plus-rules baseline. Its routing accuracy is 41.00 points
higher than the simple baseline and 4.00 points higher than the trivial
baseline.

The repaired Groq judge evaluated 200 unique responses: mean overall score
4.675/5, median 5/5, and acceptable rate 97.5%. These are automated judge
results, not human evaluation. A human calibration sample of 40 responses was
also rated using the same 1-5 overall rubric. Judge-human exact agreement was
12.5%, adjacent agreement was 25.0%, quadratic Cohen's kappa was -0.0384, and
mean absolute error was 2.5. The judge assigned 4 or 5 to 35 of 40 examples,
while the human assigned 1 or 2 to 27 examples, indicating substantial
optimism and poor agreement. The automated 97.5% acceptability figure should
therefore not be treated as validated response quality.

## 10. Error Analysis

The repaired final agent has 54 intent errors and 48 routing errors. Routing
errors contain 42 false negatives and 6 false positives.

The most frequent intent confusions are:

- `return_refund` → `product_issue` (4)
- `prime_membership` → `payment_issue` (3)
- `promotion_offer` → `other` (3)
- `customer_service` → `delivery_issue` (3)
- `customer_service` → `product_issue` (2)
- `delivery_issue` → `customer_service` (2)

The routing errors include cases where the agent auto-handled issues that were labelled for escalation, particularly refunds, seller disputes, previous-support complaints, account/security issues, and order-specific investigations.

## 11. Top Five Failure Modes

These examples are taken from `results/evaluation/error_analysis.json` and the final prediction file.

1. **`gold_0004` — Delivered product destroyed**

   A delivered product destroyed before the customer could use it was classified as `delivery_issue` instead of `product_issue`, and was auto-handled instead of escalated.

   **Hypothesis:** delivery language dominates the damaged-product signal, and the response policy does not sufficiently prioritize case-specific damage.

2. **`gold_0005` — Pre-order delivery date**

   A pre-order with no delivery date was classified as `delivery_issue` instead of `order_issue`.

   **Hypothesis:** delivery vocabulary overwhelms the pre-order/order-state signal.

3. **`gold_0014` — Wrong product after previous issue**

   A wrong phone case after a prior delivery issue was classified as `product_issue` instead of `customer_service`, and was auto-handled.

   **Hypothesis:** the concrete product complaint overwhelms the repeated-case and previous-support signal.

4. **`gold_0016` — Delivery and customer-service complaint**

   A complaint about poor delivery and customer service was classified as `customer_service` instead of `delivery_issue`, and was auto-handled.

   **Hypothesis:** broad complaint language is over-weighted relative to the operational delivery problem.

5. **`gold_0019` — Pre-order release delay**

   A pre-ordered game delayed past release was classified as `delivery_issue` instead of `order_issue`, and was auto-handled.

   **Hypothesis:** delivery timing terms dominate the pre-order/order-management distinction.

These failures suggest that the main remaining weaknesses are not basic intent recognition alone, but distinguishing overlapping transaction stages, recognizing risk-sensitive cases, and handling multilingual/security-specific messages conservatively.

## 12. What Is Misleading About My Headline Number?

The repaired 73.0% intent accuracy and 76.0% routing accuracy are measured on
200 examples sampled from a held-out test split, not the full TWCS
distribution. They depend on the selected Groq model, prompt, retrieval
corpus, provider behavior, and taxonomy. The routing score is also sensitive
to subjective escalation labels. The human calibration shows that the
automated judge is substantially more positive than the human ratings.

The result depends on the selected Groq model, prompt, historical-example
retrieval, provider behavior, and taxonomy. The golden set is fixed and
relatively small, so the reported numbers should not be interpreted as
estimates of production accuracy.

The LLM judge is not a validated quality metric in this project. On the
40-example human calibration sample, exact agreement was 12.5%, adjacent
agreement was 25.0%, quadratic Cohen's kappa was -0.0384, and mean absolute
error was 2.5. The judge was substantially more positive than the human
ratings.

These numbers demonstrate a promising prototype rather than production-level accuracy.

## 13. Decision Log

Key decisions are recorded in `results/decision_log.md`, including:

- AmazonHelp selection
- local episode reconstruction
- episode-level splitting
- the customer-overlap caveat
- rejection of naive clustering
- the 12-intent taxonomy
- both baselines
- historical retrieval
- conservative escalation
- the Gemini-to-Groq switch
- resumable evaluation
- LLM judging

The decision log also records important failed experiments and implementation trade-offs rather than only the final architecture.

## 14. What I Would Build Next Week

I would:

1. Restore the full processed AmazonHelp training split to make the retrieval corpus independently reproducible.
2. Add a small multilingual/security evaluation slice.
3. Calibrate escalation thresholds against the observed routing failures.
4. Add regression tests for the observed intent confusion pairs.
5. Compare multiple provider/model configurations under the same prompts and denominator.
6. Add retrieval-quality diagnostics to determine when historical evidence is weak or mismatched.
7. Add confidence thresholds and an explicit abstention path for uncertain or high-risk cases.

## 15. Limitations and Reproduction

Install dependencies with:

```bash
pip install -r requirements.txt