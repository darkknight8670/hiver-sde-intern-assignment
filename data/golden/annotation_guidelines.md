# AmazonHelp Golden Set Annotation Guidelines

## 1. Purpose

The golden set is the human-labelled evaluation set for the AmazonHelp
customer-support agent.

It is used to evaluate:

1. Intent classification
2. Response quality
3. Auto-handle vs human-escalation decisions

The golden set must remain separate from training and validation data.

---

## 2. Annotation Unit

The primary annotation unit is the customer's message.

Annotators should use the available conversation context when it is
necessary to understand what the customer is asking.

The historical AmazonHelp response is retained as evidence of how the
support team handled the issue historically, but it must not determine
the intent label automatically.

---

## 3. Intent Labels

### 1. delivery_issue

Problems with an order's delivery, including:

- late delivery
- missing delivery
- delayed shipment
- package not received
- misdelivery
- delivery address problems
- carrier/logistics problems

Examples:

- "My package was supposed to arrive yesterday."
- "The tracking says delivered but I haven't received it."

Do NOT use this for general order-management questions when delivery is
not the main issue.

---

### 2. order_issue

Issues involving creating, changing, cancelling, tracking the state of,
or otherwise managing an order.

Examples:

- cancelling an order
- changing an order
- checking order status
- problems placing an order
- pre-order questions

If the main problem is that an already-shipped package is late or
missing, use `delivery_issue`.

---

### 3. return_refund

Requests or problems involving:

- returning a product
- receiving a refund
- delayed refunds
- refund method
- refund amount
- exchanges related to a return

Examples:

- "When will I get my refund?"
- "I want to return this item."

---

### 4. payment_issue

Problems involving:

- payment methods
- credit/debit card payments
- cash on delivery
- unexpected charges
- duplicate charges
- Amazon Pay/payment failures

Examples:

- "I was charged twice for the same order."
- "Why is my card being declined?"

---

### 5. account_access

Problems accessing or securing an Amazon account.

Examples:

- login problems
- password problems
- OTP problems
- account locked
- account on hold
- security/access issues

---

### 6. product_issue

Problems with a physical product after ordering or receiving it.

Examples:

- defective product
- damaged product
- wrong product received
- missing component
- incomplete product

Use `product_issue` when the problem is primarily with the product
rather than the order, delivery, or return process.

---

### 7. prime_video

Technical or availability issues involving Prime Video or Amazon
digital video/content.

Examples:

- Prime Video not playing
- streaming problems
- video buffering
- device compatibility
- digital video/content availability

Important:

"Prime delivery is late" -> `delivery_issue`

"Prime Video is not working" -> `prime_video`

---

### 8. seller_marketplace

Problems involving:

- third-party sellers
- marketplace purchases
- seller communication
- seller disputes
- A-to-z claims
- seller warranties

Use this when the seller/marketplace relationship is central to the
customer's problem.

---

### 9. promotion_offer

Questions or problems involving:

- promotional offers
- discounts
- deals
- coupons
- cashback
- promotional eligibility

---

### 10. prime_membership

Questions or problems specifically about Prime membership.

Examples:

- Prime membership cancellation
- membership eligibility
- membership benefits
- Prime subscription problems

Important:

"Prime package is late" -> `delivery_issue`

"Prime Video won't play" -> `prime_video`

"How do I cancel Prime membership?" -> `prime_membership`

---

### 11. customer_service

Existing support cases where the customer primarily reports:

- poor customer support
- repeated unresolved contact
- conflicting support answers
- dissatisfaction with previous support
- request for escalation

Examples:

- "I've contacted support three times and nobody has fixed this."
- "Your customer service keeps giving me different answers."

Use this only when the support experience itself is the primary
problem.

---

### 12. other

Use `other` when the message:

- does not fit another intent
- is too unclear to classify confidently
- is general feedback
- has insufficient information to determine a specific intent

Do not use `other` simply because the message is short.

---

## 4. Ambiguous Intent Rules

When multiple intents appear in the same message, choose the intent
representing the customer's **primary problem or requested action**.

Examples:

### Delivery vs Order

"My order hasn't arrived yet."

-> `delivery_issue`

"Can I cancel my order before it ships?"

-> `order_issue`

### Delivery vs Product

"The package arrived but the item is damaged."

-> `product_issue`

"The package hasn't arrived."

-> `delivery_issue`

### Product vs Return/Refund

"The headphones are broken."

-> `product_issue`

"The headphones are broken and I want a refund."

-> `return_refund`

Use `return_refund` when the requested action is primarily the return
or refund process.

### Prime Membership vs Delivery

"Why didn't I get my Prime delivery today?"

-> `delivery_issue`

"How do I cancel my Prime membership?"

-> `prime_membership`

### Prime Video vs Prime Membership

"Prime Video isn't working."

-> `prime_video`

"I want to cancel my Prime subscription."

-> `prime_membership`

---

## 5. Confidence

Annotators should assign a confidence score:

- `high` — intent is clear
- `medium` — some ambiguity exists but one intent is more appropriate
- `low` — insufficient or highly ambiguous information

A low-confidence example should generally be labelled `other` if no
specific intent can be justified.

---

## 6. Escalation Annotation

Each example also receives a human-labelled routing decision:

- `auto_handle`
- `human_escalation`

### auto_handle

Use when the issue appears suitable for a normal support response and
does not obviously require human intervention.

Typical examples:

- delivery status questions
- standard return/refund questions
- common payment questions
- basic account-access questions
- common product issues
- straightforward Prime Video troubleshooting

### human_escalation

Use when human intervention is reasonably necessary or the situation
is high-risk/complex.

Examples include:

- unresolved repeated support interactions
- conflicting previous support responses
- account/security situations requiring verification
- serious payment disputes
- complex seller disputes
- legal/threatening language
- requests that clearly require a human decision or exception

The decision should be based on the customer's message and available
conversation context.

---

## 7. Escalation Reason

For every escalation, record a short reason.

Good:

"Customer reports repeated failed contacts and requests escalation."

"Account access issue may require identity verification."

Poor:

"Needs human."

The reason should explain the specific evidence that caused the
escalation decision.

---

## 8. Annotation Principles

Annotators should:

1. Read the customer message carefully.
2. Use conversation context when available.
3. Select exactly one primary intent.
4. Avoid inferring facts that are not present.
5. Use `other` when no intent can be justified.
6. Separate the customer's actual problem from the historical support
   response.
7. Record confidence.
8. Provide a concise rationale.
9. Make escalation decisions independently from the intent label.
10. Do not use the model's predicted label when creating the gold label.

---

## 9. Required Golden Record Fields

Each golden-set record should contain:

- `example_id`
- `conversation_id`
- `customer_message`
- `context`
- `historical_response`
- `gold_intent`
- `intent_confidence`
- `intent_rationale`
- `gold_routing`
- `routing_reason`

Optional model-generated fields may be added later, but gold labels
must remain clearly separated from model predictions.

---

## 10. Quality Control

The final golden set should contain examples from all 12 intents.

Sampling should intentionally include:

- common intents
- less frequent intents
- ambiguous examples
- short customer messages
- multi-turn examples
- examples where escalation is appropriate

The final test set must not be used for training the classifier or
retrieval system.

If an annotation is uncertain, record the uncertainty rather than
silently guessing.