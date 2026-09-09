"""
AmazonHelp Intent Taxonomy

Final manually-defined taxonomy derived from:
1. Training-set customer/support analysis
2. Candidate keyword analysis
3. Representative customer/support examples
4. AmazonHelp response patterns

IMPORTANT:
- This file defines the annotation/classification taxonomy.
- It does not inspect validation or test data.
- "other" is intentional and should be used when no intent
  can be assigned confidently.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List
import json
from pathlib import Path


@dataclass(frozen=True)
class Intent:
    id: str
    name: str
    description: str
    include: List[str]
    exclude: List[str]


INTENTS = [

    Intent(
        id="delivery_issue",
        name="Delivery problem",
        description=(
            "Problems with an order's delivery, including late, "
            "missing, delayed, misdelivered, or carrier-related shipments."
        ),
        include=[
            "order has not arrived",
            "delivery is late",
            "package is delayed",
            "tracking or carrier problem",
            "package delivered to wrong address",
            "delivery date was missed",
            "shipment was returned during delivery"
        ],
        exclude=[
            "customer wants to cancel an order",
            "customer wants a refund after receiving an item",
            "Prime Video playback problems"
        ]
    ),

    Intent(
        id="order_issue",
        name="Order management",
        description=(
            "Issues involving creating, changing, cancelling, "
            "tracking the state of, or otherwise managing an order."
        ),
        include=[
            "cancel an order",
            "order keeps getting cancelled",
            "change an order",
            "order status question",
            "pre-order question",
            "order confirmation problem"
        ],
        exclude=[
            "pure delivery delay",
            "refund-only request",
            "payment charge issue"
        ]
    ),

    Intent(
        id="return_refund",
        name="Returns and refunds",
        description=(
            "Requests or problems involving returning products, "
            "receiving refunds, refund timing, or refund method."
        ),
        include=[
            "request a return",
            "refund has not arrived",
            "refund amount is incorrect",
            "change refund method",
            "refund to gift card",
            "return eligibility",
            "exchange versus refund"
        ],
        exclude=[
            "duplicate card charge",
            "COD/payment authorization issue",
            "delivery delay without a refund request"
        ]
    ),

    Intent(
        id="payment_issue",
        name="Payment and charges",
        description=(
            "Problems involving payment methods, charges, "
            "cash on delivery, card payments, or unexpected/duplicate charges."
        ),
        include=[
            "payment failed",
            "card payment problem",
            "cash on delivery problem",
            "COD eligibility",
            "charged twice",
            "unexpected charge",
            "payment method cannot be changed",
            "Amazon Pay payment problem"
        ],
        exclude=[
            "refund status after a return",
            "general order cancellation",
            "promotion eligibility unless the issue is specifically payment"
        ]
    ),

    Intent(
        id="account_access",
        name="Account access and security",
        description=(
            "Problems accessing or securing an Amazon account."
        ),
        include=[
            "cannot log in",
            "password problem",
            "OTP/code not received",
            "old phone number prevents access",
            "account locked",
            "account on hold",
            "suspicious account activity",
            "account security problem"
        ],
        exclude=[
            "seller account issues",
            "payment method problems",
            "Prime membership questions"
        ]
    ),

    Intent(
        id="product_issue",
        name="Product problem",
        description=(
            "Problems with a physical product after ordering or receiving it."
        ),
        include=[
            "defective product",
            "damaged product",
            "wrong item received",
            "missing product components",
            "product does not work",
            "product quality problem",
            "product arrived damaged",
            "product exchange request"
        ],
        exclude=[
            "package itself is delayed",
            "refund-only issue without a product problem",
            "seller policy question"
        ]
    ),

    Intent(
        id="prime_video",
        name="Prime Video and digital content",
        description=(
            "Technical or availability issues involving Prime Video "
            "or Amazon digital video/content."
        ),
        include=[
            "Prime Video playback failure",
            "video buffering",
            "video streaming problem",
            "Prime Video app problem",
            "video device compatibility",
            "audio/video synchronization",
            "cannot watch Prime Video"
        ],
        exclude=[
            "Prime shipping or delivery",
            "Prime membership benefits",
            "physical product problems"
        ]
    ),

    Intent(
        id="seller_marketplace",
        name="Seller and marketplace",
        description=(
            "Problems involving third-party sellers, marketplace purchases, "
            "seller communication, seller disputes, or A-to-z claims."
        ),
        include=[
            "seller did not respond",
            "seller dispute",
            "seller failed to fulfill order",
            "seller charged incorrect amount",
            "A-to-z Guarantee",
            "marketplace seller complaint",
            "seller warranty issue"
        ],
        exclude=[
            "Amazon direct delivery problem",
            "Amazon account login problem",
            "general payment issue"
        ]
    ),

    Intent(
        id="promotion_offer",
        name="Promotions, deals and cashback",
        description=(
            "Questions or problems involving promotional offers, "
            "discounts, deals, coupons, or cashback."
        ),
        include=[
            "discount question",
            "deal availability",
            "coupon problem",
            "cashback eligibility",
            "cashback missing",
            "promotion terms",
            "Black Friday deals"
        ],
        exclude=[
            "ordinary payment failure",
            "Prime membership",
            "refund"
        ]
    ),

    Intent(
        id="prime_membership",
        name="Prime membership",
        description=(
            "Questions or problems specifically about Prime membership "
            "rather than Prime shipping or Prime Video."
        ),
        include=[
            "Prime membership benefits",
            "cancel Prime",
            "Prime eligibility",
            "Prime subscription problem",
            "Prime membership availability",
            "Prime service value"
        ],
        exclude=[
            "Prime delivery delay",
            "Prime Video playback",
            "ordinary order problem"
        ]
    ),

    Intent(
        id="customer_service",
        name="Customer service and escalation",
        description=(
            "Existing support cases where the customer primarily reports "
            "poor support, repeated unresolved contact, or requests escalation."
        ),
        include=[
            "previous agent did not resolve issue",
            "customer has contacted support repeatedly",
            "complaint about customer service",
            "request for escalation",
            "case has been unresolved for a long time",
            "agent provided conflicting answers"
        ],
        exclude=[
            "a new issue with a clear underlying intent",
            "simple delivery complaint unless the main complaint is unresolved support"
        ]
    ),

    Intent(
        id="other",
        name="Other or unclear",
        description=(
            "Amazon-related customer message that cannot be confidently "
            "assigned to another intent."
        ),
        include=[
            "ambiguous request",
            "general Amazon question",
            "feedback without a clear support problem",
            "message containing insufficient information"
        ],
        exclude=[]
    )
]


INTENT_BY_ID: Dict[str, Intent] = {
    intent.id: intent
    for intent in INTENTS
}


def get_intents() -> List[Intent]:
    """
    Return the complete taxonomy.
    """

    return INTENTS


def get_intent(intent_id: str) -> Intent:
    """
    Return an intent by ID.
    """

    if intent_id not in INTENT_BY_ID:

        raise ValueError(
            f"Unknown intent: {intent_id}"
        )

    return INTENT_BY_ID[intent_id]


def intent_ids() -> List[str]:
    """
    Return intent IDs in stable order.
    """

    return [
        intent.id
        for intent in INTENTS
    ]


def export_taxonomy(
    output_path="results/intent_taxonomy.json"
):
    """
    Export the taxonomy as JSON for evaluation and annotation.
    """

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    data = {
        "taxonomy_version": "1.0",
        "brand": "AmazonHelp",
        "num_intents": len(INTENTS),
        "intents": [
            asdict(intent)
            for intent in INTENTS
        ]
    }

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved taxonomy to {output_path}"
    )


def print_taxonomy():

    print()
    print("=" * 70)
    print("AMAZONHELP INTENT TAXONOMY")
    print("=" * 70)

    for i, intent in enumerate(
        INTENTS,
        start=1
    ):

        print(
            f"\n{i}. {intent.id}"
        )

        print(
            f"   {intent.name}"
        )

        print(
            f"   {intent.description}"
        )

    print()
    print(
        f"Total intents: {len(INTENTS)}"
    )


if __name__ == "__main__":

    print_taxonomy()

    export_taxonomy()