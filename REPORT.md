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
2. Include the retrieved evidence and conversation context in the prompt.
3. Ask the selected LLM to classify intent, select routing, and draft a response.
4. Parse and validate a fixed JSON schema.

The final provider was Groq using `openai/gpt-oss-120b`. Gemini remains supported as an alternative provider. The final agent uses historical-example retrieval followed by LLM generation; the committed predictions contain populated retrieved examples with similarity scores.

## 5. What I Did Not Build

This is not a production support system. It does not provide live Twitter integration, Amazon account or order access, real refunds, production authentication, persistent customer memory, real-time policy verification, agent dashboards, monitoring, or deployment infrastructure.

## 6. Evaluation Design

The fixed 200-example golden set is joined by `example_id`. All baseline and agent classification metrics use the same denominator. Failed API calls are excluded rather than fabricated. The final agent has 200 successful unique predictions. The LLM judge evaluates only real agent predictions and does not use the gold intent to score response quality.

## 7. Baselines

The trivial baseline predicts the majority intent and always escalates. The retrieval-plus-rules baseline uses TF-IDF retrieval and deterministic keyword/routing rules. The final agent uses the provider-backed structured LLM path.

## 8. Final Results

| System | N | Intent accuracy | Intent macro-F1 | Intent weighted-F1 | Routing accuracy | Routing macro-F1 | Routing weighted-F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Trivial | 200 | 15.50% | 2.24% | 4.16% | 72.00% | 41.86% | 60.28% |
| Retrieval + rules | 200 | 53.00% | 51.81% | 53.33% | 35.00% | 32.00% | 25.72% |
| Final Groq agent | 200 | **71.50%** | **68.66%** | **71.43%** | **85.50%** | **83.54%** | **86.04%** |

The final Groq agent improves intent accuracy by 18.50 percentage points over the retrieval-plus-rules baseline and by 56.00 percentage points over the trivial baseline. Routing accuracy improves by 50.50 percentage points over the retrieval-plus-rules baseline.

The genuine Groq LLM judge evaluated 200 responses using the stated rubric. Mean overall score was 4.64/5, median 5/5, and acceptable rate 96.0%. These are automated judge results, not human evaluation. The judge was not independently calibrated against human ratings, so human-judge agreement is not reported.

## 9. Error Analysis

The final agent has 57 intent errors and 29 routing errors. Routing errors contain 24 false negatives and 5 false positives.

The most frequent intent confusions are:

- `return_refund` → `product_issue` (4)
- `prime_membership` → `payment_issue` (3)
- `promotion_offer` → `other` (3)
- `customer_service` → `delivery_issue` (3)
- `customer_service` → `product_issue` (2)
- `delivery_issue` → `customer_service` (2)

The routing errors include cases where the agent auto-handled issues that were labelled for escalation, particularly refunds, seller disputes, previous-support complaints, account/security issues, and order-specific investigations.

## 10. Top Five Failure Modes

These examples are taken from `results/evaluation/error_analysis.json` and the final prediction file.

1. **`gold_0030` — Missing product and refund**

   A missing product and uninitiated refund was classified as `delivery_issue` instead of `return_refund`.

   **Hypothesis:** multiple transaction stages compete in the same message, and the refund clause was underweighted.

2. **`gold_0037` — Damaged product versus refund workflow**

   Broken desks with a return-cost and refund complaint was classified as `product_issue` instead of `return_refund`.

   **Hypothesis:** product damage dominated the explicit return/refund workflow.

3. **`gold_0055` — Prime charge**

   An unrecognized Prime charge was classified as `payment_issue` instead of `prime_membership`.

   **Hypothesis:** charge language obscured the membership-specific intent.

4. **`gold_0113` — Fraudulent third-party seller**

   A suspected fraudulent third-party seller was auto-handled instead of escalated.

   **Hypothesis:** seller detection worked, but the risk and case-specific routing policy was too weak.

5. **`gold_0182` — Multilingual phishing/security message**

   A Japanese phishing SMS was classified as `other` instead of `account_access` and auto-handled.

   **Hypothesis:** multilingual and security-related language is poorly represented by the English-oriented prompt/retrieval setup.

These failures suggest that the main remaining weaknesses are not basic intent recognition alone, but distinguishing overlapping transaction stages, recognizing risk-sensitive cases, and handling multilingual/security-specific messages conservatively.

## 11. What Is Misleading About My Headline Number?

The 71.5% intent accuracy and 85.5% routing accuracy are measured on a 200-example evaluation set sampled from a held-out test split rather than representing the full TWCS distribution.

The result depends on the selected Groq model, prompt, historical-example retrieval, provider behavior, and taxonomy. The golden set is fixed and relatively small, so the reported numbers should not be interpreted as estimates of production accuracy.

The LLM judge provides an additional automated quality signal, not a production guarantee. It was not independently calibrated against human ratings, so its agreement with human reviewers is unknown.

These numbers demonstrate a promising prototype rather than production-level accuracy.

## 12. Decision Log

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

## 13. What I Would Build Next Week

I would:

1. Restore the full processed AmazonHelp training split to make the retrieval corpus independently reproducible.
2. Add a small multilingual/security evaluation slice.
3. Calibrate escalation thresholds against the observed routing failures.
4. Add regression tests for the observed intent confusion pairs.
5. Compare multiple provider/model configurations under the same prompts and denominator.
6. Add retrieval-quality diagnostics to determine when historical evidence is weak or mismatched.
7. Add confidence thresholds and an explicit abstention path for uncertain or high-risk cases.

## 14. Limitations and Reproduction

Install dependencies with:

```bash
pip install -r requirements.txt