import re


_PATTERNS = {
    "email":       re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "phone":       re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn":         re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
}


def redact(text: str, replacement: str = "[REDACTED]") -> str:
    """Replace detected PII patterns with a placeholder."""
    for _name, pattern in _PATTERNS.items():
        if _name == "credit_card":
            # For credit cards, mask all but the last 4 digits
            text = mask_credit_cards(text,pattern)
        text = pattern.sub(replacement, text)
    return text


def detect(text: str) -> list[str]:
    """Return a list of PII type names found in text."""
    return [name for name, pattern in _PATTERNS.items() if pattern.search(text)]



def mask_credit_cards(text: str, pattern: re.Pattern) -> str:
    def replace(m: re.Match) -> str:
        digits = re.sub(r"[ -]", "", m.group())
        if len(digits) < 13 or len(digits) > 19:
            return m.group()
        return f"****-****-****-{digits[-4:]}"

    return pattern.sub(replace, text)