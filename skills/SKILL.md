# Agent Skills

This document describes the reusable skills available to the fraud detection agent.

## transaction_history_lookup
- **Module**: `tools/tool_search.py`
- **Description**: Fetches the last 30 transactions for a given `user_id` from the SQLite database and returns aggregated stats (avg/max/min amount, fraud rate, locations, categories).
- **Input**: `user_id: str`
- **Output**: JSON string with user behavioral summary.

## escalate_case
- **Module**: `tools/tool_escalate.py`
- **Description**: Routes a high-risk transaction to the human fraud review team and logs the escalation event.
- **Input**: `transaction_id: str`, `reason: str`, `risk_score: int`
- **Output**: JSON confirmation with escalation status.

## retrieve_knowledge
- **Module**: `retrieval/retriever.py`
- **Description**: Retrieves relevant document chunks from the FAISS knowledge base using semantic search.
- **Input**: `query: str`, `top_k: int = 5`
- **Output**: List of matching document chunks with source and text.
