import re
from safety.pii_filter import redact
    

BLOCKED_PHRASES = [
    "ignore previous instructions",
    "disregard your instructions",
    "you are now",
    "act as",
    "jailbreak",
]


class Guardrails:
    """Input/output guardrails to prevent prompt injection and mask PII."""

    def check_input(self, text: str) -> tuple[bool, str]:
        """Returns (is_safe, reason). is_safe=False means the input is blocked."""
        lower = text.lower()
        for phrase in BLOCKED_PHRASES:
            if phrase in lower:
                return False, f"Blocked phrase detected: '{phrase}'"
        return True, ""

    def check_output(self, text: str) -> tuple[bool, str]:
        """Returns (is_safe, reason). is_safe=False means the output should not be returned."""
        return True, ""

    def sanitize(self, text: str) -> str:
        """Strip control characters from user input."""
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    def mask_pii(self, text: str) -> str:
        """Replace credit card and bank account numbers with masked placeholders."""
        text = redact(text)
        return text


    # def _mask_bank_accounts(self, text: str) -> str:
    #     def replace(m: re.Match) -> str:
    #         account = m.group(1)
    #         masked = "*" * (len(account) - 4) + account[-4:]
    #         return m.group().replace(account, masked)

    #     return _BANK_ACCOUNT_PATTERN.sub(replace, text)
