from bs4 import BeautifulSoup
from .config import settings

# Tags that contribute noise but no extractable data
_NOISE_TAGS = [
    "script", "style", "noscript", "iframe", "svg",
    "nav", "footer", "header", "aside", "form",
    "button", "input", "select", "textarea",
    "advertisement", "cookie-banner",
]

_NOISE_ATTRS = {"class": ["ad", "ads", "advertisement", "cookie", "popup",
                           "modal", "banner", "sidebar", "promo"]}


def strip_html(raw_html: str) -> str:
    """
    Remove all noise from raw HTML before sending to Claude.
    Strategy: BeautifulSoup decompose → plain text extraction.
    Reduces token payload by 30–60% on average.
    """
    soup = BeautifulSoup(raw_html, "lxml")

    # Remove noisy structural tags
    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    # Remove elements with noise CSS classes
    for attr, values in _NOISE_ATTRS.items():
        for value in values:
            for el in soup.find_all(attrs={attr: lambda v, val=value: v and val in v}):
                el.decompose()

    return soup.get_text(separator="\n", strip=True)


def truncate_to_token_limit(text: str, max_chars: int = None) -> str:
    """
    Rough char-to-token guard (1 token ≈ 4 chars).
    Prevents sending oversized payloads to Claude.
    """
    limit = max_chars or (settings.max_token_input * 4)
    return text[:limit] if len(text) > limit else text


def preprocess(raw_html: str) -> str:
    """Full preprocessing pipeline: strip → truncate."""
    text = strip_html(raw_html)
    return truncate_to_token_limit(text)
