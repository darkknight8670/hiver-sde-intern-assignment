import json
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


TRAIN_PATH = Path("data/processed/splits/train.jsonl")


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class HistoricalRetriever:

    def __init__(
        self,
        train_path=TRAIN_PATH,
        max_features=100000,
    ):
        self.train_path = Path(train_path)

        episodes = load_jsonl(self.train_path)

        self.messages = []
        self.responses = []

        self._build_corpus(episodes)

        if not self.messages:
            raise RuntimeError(
                "No customer/support pairs found in training data."
            )

        self.vectorizer = TfidfVectorizer(
            preprocessor=normalize_text,
            ngram_range=(1, 2),
            min_df=2,
            max_features=max_features,
            sublinear_tf=True,
        )

        self.matrix = self.vectorizer.fit_transform(
            self.messages
        )

        print(
            f"HistoricalRetriever initialized with "
            f"{len(self.messages):,} examples."
        )

        print(
            f"TF-IDF vocabulary: "
            f"{len(self.vectorizer.vocabulary_):,}"
        )

    def _build_corpus(self, episodes):

        for episode in episodes:

            turns = episode.get("turns", [])

            for i, turn in enumerate(turns):

                if turn.get("speaker") != "customer":
                    continue

                customer_message = (
                    turn.get("text", "").strip()
                )

                if not customer_message:
                    continue

                # Find the first support response after
                # this customer message.
                support_response = None

                for next_turn in turns[i + 1:]:

                    if next_turn.get("speaker") == "support":

                        support_response = (
                            next_turn.get("text", "").strip()
                        )

                        break

                if not support_response:
                    continue

                self.messages.append(
                    customer_message
                )

                self.responses.append(
                    support_response
                )

    def retrieve(
        self,
        query,
        top_k=5,
    ):
        """
        Return the top-k historically similar
        customer/support examples.
        """

        if not query or not query.strip():
            return []

        query_vector = self.vectorizer.transform(
            [query]
        )

        similarities = cosine_similarity(
            query_vector,
            self.matrix
        )[0]

        # Get top-k indices efficiently.
        top_indices = similarities.argsort()[
            ::-1
        ][:top_k]

        results = []

        for index in top_indices:

            results.append({
                "customer_message": self.messages[index],
                "historical_response": self.responses[index],
                "similarity": float(
                    similarities[index]
                ),
            })

        return results


if __name__ == "__main__":

    retriever = HistoricalRetriever()

    query = input(
        "\nEnter a customer message: "
    ).strip()

    results = retriever.retrieve(
        query,
        top_k=5,
    )

    print("\n" + "=" * 70)
    print("HISTORICAL MATCHES")
    print("=" * 70)

    for i, result in enumerate(results, 1):

        print(f"\n--- Match {i} ---")
        print(
            f"Similarity: "
            f"{result['similarity']:.4f}"
        )

        print(
            f"Customer:\n"
            f"{result['customer_message']}"
        )

        print(
            f"\nAmazonHelp:\n"
            f"{result['historical_response']}"
        )