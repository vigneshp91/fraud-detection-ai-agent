"""
Langfuse v4 observability client.

Wraps the Langfuse SDK to provide a context-manager-based trace API used by
the evaluation harness and the production deployment.  Gracefully degrades to
a no-op when keys are absent or the package is not installed.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Iterator

logger = logging.getLogger(__name__)


class _NoopObs:
    """Stand-in for a LangfuseSpan when tracing is disabled."""
    def update(self, **_): pass
    def score(self, **_): pass
    def score_trace(self, **_): pass
    def set_trace_io(self, **_): pass
    def end(self, **_): pass


class LangfuseLogger:
    """
    Thin wrapper around the Langfuse v4 Python SDK.

    Usage
    -----
    tracer = LangfuseLogger()

    with tracer.observe("eval/tc_001", as_type="evaluator", input=tx) as obs:
        result = run_crew(tx)
        obs.update(output=result)
        obs.score_trace(name="correctness", value=1.0, comment="...")
        obs.score_trace(name="latency_s",   value=2.4)

    tracer.flush()
    """

    def __init__(self) -> None:
        self._client = None
        self._setup()

    def _setup(self) -> None:
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        host       = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if not public_key or not secret_key:
            logger.warning("LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY not set — tracing disabled.")
            return

        try:
            from langfuse import Langfuse
            self._client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
            )
            logger.info("Langfuse v4 tracing enabled (host=%s).", host)
        except ImportError:
            logger.warning("langfuse package not installed — run: pip install 'langfuse>=3.0.0'")

    def is_enabled(self) -> bool:
        return self._client is not None

    @contextmanager
    def observe(
        self,
        name: str,
        as_type: str = "span",
        input: Any = None,
        metadata: dict | None = None,
    ) -> Iterator:
        """
        Context manager that opens a Langfuse observation (trace root) and
        yields the span object.  Callers use span.update(), span.score_trace(),
        and span.score() inside the block.

        Falls back to a no-op _NoopObs when tracing is disabled.
        """
        if self._client is None:
            yield _NoopObs()
            return

        kwargs: dict = dict(name=name, as_type=as_type)
        if input is not None:
            kwargs["input"] = input
        if metadata:
            kwargs["metadata"] = metadata

        with self._client.start_as_current_observation(**kwargs) as obs:
            yield obs

    def flush(self) -> None:
        """Block until all queued events are delivered to Langfuse."""
        if self._client is not None:
            self._client.flush()
