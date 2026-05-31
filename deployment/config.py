import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_title: str = "AI Fraud Detection Agent"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")


settings = Settings()
