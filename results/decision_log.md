# Decision Log

## 1\. Brand selection: AmazonHelp

Selected AmazonHelp as the target brand because it has a large number of support interactions in the TWCS dataset and provides broad coverage of delivery, order, payment, account, product, Prime, and marketplace issues.

## 2\. Conversation reconstruction: local support episodes

The initial root-thread reconstruction produced very long conversations containing multiple unrelated support topics. We therefore switched to local reply-chain episodes centered on customer messages directly answered by AmazonHelp.

## 3\. Alternating customer/support structure

Episodes follow direct customer-to-AmazonHelp reply relationships rather than treating an entire Twitter thread as one support case. This better represents individual customer-support interactions.

## 4\. Episode-level train/validation/test split

We split reconstructed episodes into train, validation, and test sets rather than splitting individual tweets. This prevents tweets from the same reconstructed episode from appearing across multiple splits.

## 5\. Random 70/15/15 split

We used a random episode-level 70/15/15 split. Some customer accounts appear across splits because TWCS reply chains can contain multiple customer accounts; however, tweet overlap across splits is zero.

## 6\. Intent taxonomy design

We defined 12 support intents: delivery\_issue, order\_issue, return\_refund, payment\_issue, account\_access, product\_issue, prime\_video, seller\_marketplace, promotion\_offer, prime\_membership, customer\_service, and other.

The taxonomy was designed from observed customer/support language and intended to remain small enough for reliable annotation.

## 7\. Naive TF-IDF clustering was rejected

K-means clustering over TF-IDF representations produced highly imbalanced clusters, with most examples concentrated in only a few clusters. We therefore did not use unsupervised clusters as the final intent taxonomy.

## 8\. Golden evaluation set

We created a fixed 200-example golden set covering the 12 intents and ambiguous cases. The set is sampled from the held-out test split and includes intent, routing, and rationale annotations.

## 9\. Trivial baseline

The trivial baseline always predicts the majority intent and always escalates to a human. This establishes a simple lower-bound reference.

## 10\. Retrieval/rule baseline

The second baseline combines TF-IDF retrieval over historical AmazonHelp customer/support pairs with deterministic keyword-based intent and routing rules. This tests whether historical examples and lightweight heuristics provide value before using an LLM.

## 11\. Retrieval-augmented generation

The final agent retrieves similar historical AmazonHelp interactions and provides them as evidence to the language model. This was chosen to reduce unsupported responses and ground the generated reply in observed historical support behavior.

## 12\. Conservative escalation

The agent is instructed to prefer human escalation when resolving an issue requires account-specific or order-specific investigation that cannot safely be performed from a public Twitter interaction.

## 13\. Structured agent output

The agent returns a fixed JSON schema containing intent, routing, routing\_reason, and response. This makes the system easier to evaluate automatically and separates classification/routing decisions from the generated text.

## 14\. Initial Gemini provider

Gemini was used during initial development because a supported API model was available for experimentation. Its applicable request quota interrupted the first batch after 14 successful predictions; those preliminary records were preserved but are not the final headline evaluation.

## 15\. Groq provider switch

The final batch and judge used the official Groq Python SDK with an explicit provider switch, `LLM_PROVIDER=groq`, and model `openai/gpt-oss-120b`. The agent's JSON schema and 12-intent taxonomy were kept unchanged.

## 16\. Resumable evaluation

The agent and judge evaluators preserve successful example IDs, retry transient provider failures with bounded backoff, and do not write failed predictions as completed results. The final artifacts contain 200 unique agent predictions and 200 unique genuine judge records.

## 17\. LLM-as-judge scope

The judge scores groundedness, helpfulness, correctness, tone, hallucination, overall quality, acceptability, and reason using only each real agent record. Mock or synthetic judge records are excluded from the final count.
