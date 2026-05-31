from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field


@dataclass
class ConversationMemory:
    """Lightweight in-process memory for multi-turn agent sessions."""
    max_turns: int = 20
    _history: deque = field(default_factory=lambda: deque(maxlen=20))

    def add(self, role: str, content: str) -> None:
        self._history.append({"role": role, "content": content})

    def get_history(self) -> list[dict]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)
