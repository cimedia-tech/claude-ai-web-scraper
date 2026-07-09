import json
from typing import Type
from anthropic import Anthropic
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import settings
from .cache import URLCache


# System prompt is defined once — cached via cache_control to save 90% on reused input
_SYSTEM_PROMPT = {
    "type": "text",
    "text": (
        "You are a precise data extraction engine. "
        "The user will send you web page content (cleaned text or Markdown). "
        "Extract the requested data and return ONLY a valid JSON array. "
        "Each element must match the provided schema exactly. "
        "If a field cannot be found, set it to null. "
        "Do not include explanations, markdown fences, or extra text — pure JSON array only."
    ),
    "cache_control": {"type": "ephemeral"},  # Prompt caching — up to 90% input savings
}


class ClaudeExtractor:
    """
    Wrapper around Anthropic SDK for structured web data extraction.
    Implements:
      - Prompt caching (system prompt cached as ephemeral)
      - Cost logging per call
      - Retry with exponential backoff on rate limits
      - Pydantic schema validation on output
    """

    def __init__(self, cache: URLCache = None):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.cache = cache

    def _build_user_prompt(self, content: str, schema: Type[BaseModel],
                           instruction: str) -> str:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        return (
            f"INSTRUCTION: {instruction}\n\n"
            f"EXTRACTION SCHEMA:\n{schema_json}\n\n"
            f"PAGE CONTENT:\n{content}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _call_claude(self, user_content: str) -> tuple[str, int, int]:
        """Raw Claude API call. Returns (text, input_tokens, output_tokens)."""
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens,
            system=[_SYSTEM_PROMPT],
            messages=[{"role": "user", "content": user_content}],
        )
        text = response.content[0].text
        return text, response.usage.input_tokens, response.usage.output_tokens

    async def extract(
        self,
        content: str,
        schema: Type[BaseModel],
        url: str = "",
        instruction: str = "Extract all relevant items from this page.",
    ) -> list[BaseModel]:
        """
        Extract structured data from preprocessed page content.
        Validates output against Pydantic schema.
        Returns list of validated model instances.
        """
        user_prompt = self._build_user_prompt(content, schema, instruction)
        raw_text, input_tok, output_tok = await self._call_claude(user_prompt)

        # Log cost
        if self.cache:
            cost = await self.cache.log_cost(
                url, settings.claude_model, input_tok, output_tok
            )

        # Parse + validate
        try:
            # Strip markdown fences if model adds them despite instructions
            clean = raw_text.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            raw_list = json.loads(clean)
            if not isinstance(raw_list, list):
                raw_list = [raw_list]
            return [schema(**item) for item in raw_list]
        except Exception as e:
            raise ValueError(
                f"Claude output validation failed: {e}\nRaw output: {raw_text[:500]}"
            )
