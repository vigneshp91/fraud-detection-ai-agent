import os
import logging

logger = logging.getLogger(__name__)


class LangSmithTracer:
    """Wraps LangSmith tracing for agent runs."""

    def __init__(self):
        self.api_key = os.getenv("LANGSMITH_API_KEY", "")
        self.project = os.getenv("LANGSMITH_PROJECT", "fraud-detection-agent")
        self._client = None
        self._setup()

    def _setup(self):
        if not self.api_key:
            logger.warning("LANGSMITH_API_KEY not set — tracing disabled.")
            return
        try:
            from langsmith import Client
            self._client = Client(api_key=self.api_key)
            os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
            os.environ.setdefault("LANGCHAIN_PROJECT", self.project)
            logger.info("LangSmith tracing enabled for project: %s", self.project)
        except ImportError:
            logger.warning("langsmith package not installed — tracing disabled.")

    def is_enabled(self) -> bool:
        return self._client is not None
