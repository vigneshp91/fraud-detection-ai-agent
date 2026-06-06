import json, os, time, traceback, uuid
from typing import Any, Dict

def _ensure_log_dir():
    d = os.path.dirname("logs/interactions.log")
    if d:
        os.makedirs(d, exist_ok=True)

def new_request_id() -> str:
    return str(uuid.uuid4())

def log_event(event: str, request_id: str, level: str = "INFO", **fields: Any) -> None:
    _ensure_log_dir()
    payload: Dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": level,
        "request_id": request_id,
        "event": event,
        **fields,
    }
    with open("logs/interactions.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

def log_exception(event: str, request_id: str, exc: BaseException, **fields: Any) -> None:
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-4000:]
    log_event(
        event=event,
        request_id=request_id,
        level="ERROR",
        error_type=type(exc).__name__,
        error_message=str(exc),
        traceback=tb,
        **fields,
    )
