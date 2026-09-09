import os

from dotenv import load_dotenv
from google import genai
from groq import Groq


load_dotenv()


class LLMProvider:
    """Small adapter for the supported text-generation providers."""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()

        if self.provider == "groq":
            self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY is not set in .env")
            self.client = Groq(api_key=api_key)
        elif self.provider == "gemini":
            self.model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY is not set in .env")
            self.client = genai.Client(api_key=api_key)
        else:
            raise RuntimeError(
                f"Unsupported LLM_PROVIDER: {self.provider}. "
                "Use 'groq' or 'gemini'."
            )

    def generate(self, system_prompt, user_prompt):
        if self.provider == "groq":
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            return completion.choices[0].message.content or ""

        interaction = self.client.interactions.create(
            model=self.model,
            input=f"{system_prompt}\n\n{user_prompt}",
        )
        return interaction.output_text or ""
