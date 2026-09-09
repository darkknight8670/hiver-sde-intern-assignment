# Hiver SDE Intern Assignment Report

## 1. Problem Framing

This project builds an offline AmazonHelp customer-support assistant. Given a customer message and optional context, it predicts one of 12 support intents, chooses `auto_handle` or `human_escalation`, and drafts a concise response grounded in historical support behavior.

The goal is not to claim production automation. It is to compare a structured retrieval/rules baseline with a retrieval-augmented language-model agent under a fixed evaluation protocol.

## 2. Dataset and Episode Construction

The source is Customer Support on Twitter (TWCS). AmazonHelp was selected because it has broad support coverage across delivery, orders, payments, accounts, products, Prime, and marketplace issues. Conversations were reconstructed as local customer-to-AmazonHelp support episodes. A root-thread approach was rejected because it produced long threads containing unrelated cases.

The data split is random and episode-level: 70% train, 15% validation, and 15% test. Tweet overlap across splits is zero, although customer-account overlap is possible. The golden set contains 200 examples sampled from the held-out test split.

Golden annotations were prepared through the project's annotation/model-assisted workflow. Independent human validation was not completed.

## 3. Intent Taxonomy

The fixed taxonomy has 12 intents:

`delivery_issue`, `order_issue`, `return_refund`, `payment_issue`, `account_access`, `product_issue`, `prime_video`, `seller_marketplace`, `promotion_offer`, `prime_membership`, `customer_service`, and `other`.

## 4. Agent Architecture

The intended architecture is:

1. Retrieve similar historical AmazonHelp customer/support pairs with TF-IDF.
2. Include the retrieved evidence and conversation context in the prompt.
3. Ask the selected LLM to classify intent, select routing, and draft a response.
4. Parse and validate a fixed JSON schema.

The final provider was Groq using `openai/gpt-oss-120b` through the official Groq SDK. Gemini remains supported as an alternative provider. The final agent uses historical-example retrieval followed by LLM generation; the committed predictions contain populated retrieved examples with similarity scores.

## 5. What I Did Not Build

This is not a production support system. It does not provide live Twitter integration, Amazon account or order access, real refunds, production authentication, persistent customer memory, real-time policy verification, agent dashboards, monitoring, or deployment infrastructure.

## 6. Evaluation Design

The fixed 200-example golden set is joined by `example_id`. All baseline and agent classification metrics use the same denominator. Failed API calls are excluded rather than fabricated. The final agent has 200 successful unique predictions. The LLM judge evaluates only real agent predictions and does not use the gold intent to score response quality.

Human review was not completed for this submission. Therefore human-judge agreement is not reported.

## 7. Baselines

The trivial baseline predicts the majority intent and always escalates. The retrieval-plus-rules baseline uses TF-IDF retrieval and deterministic keyword/routing rules. The final agent uses the provider-backed structured LLM path.

## 8. Final Results

| System | N | Intent accuracy | Intent macro-F1 | Intent weighted-F1 | Routing accuracy | Routing macro-F1 | Routing weighted-F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Trivial | 200 | 15.50% | 2.24% | 4.16% | 72.00% | 41.86% | 60.28% |
| Retrieval + rules | 200 | 53.00% | 51.81% | 53.33% | 35.00% | 32.00% | 25.72% |
| Final Groq agent | 200 | 71.50% | 68.66% | 71.43% | 85.50% | 83.54% | 86.04% |

The genuine Groq LLM judge evaluated 200 responses using the stated rubric. Mean overall score was 4.64/5, median 5/5, and acceptable rate 96.0%. These are automated judge results, not human evaluation.

## 9. Error Analysis

The final agent has 57 intent errors and 29 routing errors. Routing errors contain 24 false negatives and 5 false positives. The most frequent intent confusions are return/refund to product issue, Prime membership to payment issue, promotion offer to other, and customer service to delivery issue.

## 10. Top Five Failure Modes

These examples are taken from `results/evaluation/error_analysis.json` and the final prediction file:

1. `gold_0030`: a missing product and uninitiated refund was classified as `delivery_issue` instead of `return_refund`. Hypothesis: multiple transaction stages compete, and the refund clause was underweighted.
2. `gold_0037`: broken desks with a return-cost and refund complaint was classified as `product_issue` instead of `return_refund`. Hypothesis: product damage dominated the explicit return/refund workflow.
3. `gold_0055`: an unrecognized Prime charge was classified as `payment_issue` instead of `prime_membership`. Hypothesis: charge language obscured the membership-specific intent.
4. `gold_0113`: a suspected fraudulent third-party seller was auto-handled instead of escalated. Hypothesis: seller detection worked, but the risk and case-specific routing policy was too weak.
5. `gold_0182`: a Japanese phishing SMS was classified as `other` instead of `account_access` and auto-handled. Hypothesis: multilingual and security-related language is poorly represented by the English-oriented prompt/retrieval setup.

## 11. What Is Misleading About My Headline Number?

The 71.5% intent accuracy and 85.5% routing accuracy are measured on a 200-example evaluation set whose annotations were not independently human-validated. The set is sampled from a held-out test split rather than representing the full TWCS distribution. The result depends on the selected Groq model, prompt, historical-example retrieval, provider behavior, and taxonomy. The LLM judge provides an additional automated quality signal, but it is not a substitute for human agreement. These numbers demonstrate a promising prototype rather than production-level accuracy.

## 12. Decision Log

Key decisions are recorded in `results/decision_log.md`, including AmazonHelp selection, local episode reconstruction, episode-level splitting, the customer-overlap caveat, rejection of naive clustering, the 12-intent taxonomy, both baselines, historical retrieval, conservative escalation, the Gemini-to-Groq switch, resumable evaluation, LLM judging, and the human-review limitation.

## 13. What I Would Build Next Week

I would restore the full processed AmazonHelp training split to make the retrieval corpus independently reproducible, add a small multilingual/security evaluation slice, and have an independent reviewer annotate a blinded sample. I would then calibrate escalation thresholds against human labels, add regression tests for the observed confusion pairs, and compare multiple provider/model configurations under the same prompts and denominator.

## 14. Limitations and Reproduction

Install dependencies with `pip install -r requirements.txt`, copy `.env.example` to `.env`, and set the provider key. The committed baseline and evaluation artifacts reproduce the reported metrics without API access:

```bash
python -m src.evaluation.metrics
python -m src.evaluation.compare
python -m src.evaluation.error_analysis
```

To rerun model calls, set `LLM_PROVIDER=groq`, `GROQ_MODEL=openai/gpt-oss-120b`, and `GROQ_API_KEY`, then run:

```bash
python -m src.evaluation.run_agent
python -m src.evaluation.judge
```

The full TWCS CSV and generated processed JSONL files are intentionally excluded from git because of size. The committed final predictions contain populated historical retrieval examples; obtain the dataset and run the documented data pipeline to rebuild the retrieval corpus for an independent rerun.
