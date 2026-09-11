import json

from dotenv import load_dotenv

from retrieve import HistoricalRetriever
from prompts import SYSTEM_PROMPT, build_user_prompt
from provider import LLMProvider


load_dotenv()


class SupportAgent:
    def __init__(self):
        self.provider = LLMProvider()
        self.retriever = HistoricalRetriever()

    def predict(self, customer_message, context=None):

        # Retrieve historically similar AmazonHelp conversations
        retrieved = self.retriever.retrieve(
            customer_message,
            top_k=5
        )

        # Build the prompt using the customer message,
        # conversation context, and historical examples
        user_prompt = build_user_prompt(
            customer_message,
            context or [],
            retrieved
        )

        # Call Gemini
        raw_output = self.provider.generate(
            SYSTEM_PROMPT,
            user_prompt,
        ).strip()

        if not raw_output:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        # Remove accidental Markdown JSON fences
        if raw_output.startswith("```"):
            lines = raw_output.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            raw_output = "\n".join(lines).strip()

        # Parse JSON
        try:
            result = json.loads(raw_output)

        except json.JSONDecodeError as e:
            print("\nRAW GEMINI OUTPUT:")
            print(raw_output)

            raise RuntimeError(
                f"Gemini returned invalid JSON: {e}"
            )

        # Valid intent labels
        valid_intents = {
            "delivery_issue",
            "order_issue",
            "return_refund",
            "payment_issue",
            "account_access",
            "product_issue",
            "prime_video",
            "seller_marketplace",
            "promotion_offer",
            "prime_membership",
            "customer_service",
            "other",
        }

        # Valid routing decisions
        valid_routing = {
            "auto_handle",
            "human_escalation",
        }

        # Validate intent
        if result.get("intent") not in valid_intents:
            raise ValueError(
                f"Invalid intent: {result.get('intent')}"
            )

        # Validate routing
        if result.get("routing") not in valid_routing:
            raise ValueError(
                f"Invalid routing: {result.get('routing')}"
            )

        # Required response fields
        required_fields = [
            "intent",
            "routing",
            "routing_reason",
            "response",
        ]

        for field in required_fields:
            if field not in result:
                raise ValueError(
                    f"Missing field: {field}"
                )

        return {
            "intent": result["intent"],
            "routing": result["routing"],
            "routing_reason": result["routing_reason"],
            "response": result["response"],
            "retrieved_examples": retrieved,
            "provider": self.provider.provider,
            "model": self.provider.model,
        }


def main():

    agent = SupportAgent()

    print("AmazonHelp AI Support Agent")
    print("Type 'exit' to quit.\n")

    while True:

        message = input("Customer: ")

        if message.lower().strip() == "exit":
            break

        if not message.strip():
            continue

        try:

            result = agent.predict(message)

            print("\n--- Agent ---")
            print("Intent:", result["intent"])
            print("Routing:", result["routing"])
            print(
                "Reason:",
                result["routing_reason"]
            )
            print(
                "Response:",
                result["response"]
            )
            print()

        except Exception as e:

            print("\nError:", e)
            print()


if __name__ == "__main__":
    main()