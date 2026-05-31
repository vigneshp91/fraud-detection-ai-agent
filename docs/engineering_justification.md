# Engineering Justification

## Architecture Choices

### Multi-Agent with Sequential Process
A single monolithic prompt struggles to simultaneously flag anomalies, retrieve history, score risk, and format output. Decomposing into four specialist agents (Monitor → Analyst → Risk Scorer → Orchestrator) allows each to focus on a single concern, improving quality and debuggability.

### CrewAI Framework
CrewAI provides native support for sequential task pipelines, inter-agent context passing, and tool integration — exactly what this workflow requires — without the overhead of building orchestration from scratch.

### SQLite for Transaction History
A lightweight SQLite database is sufficient for the demo scale (3 users, ~1,000 transactions). The `TransactionHistoryTool` wraps it as a CrewAI tool, making history lookup a first-class agent capability.

### FastAPI for Deployment
FastAPI gives us async request handling, automatic OpenAPI docs, and Pydantic model validation with minimal boilerplate. The crew runs in a thread pool via `asyncio.to_thread` to keep the event loop non-blocking.

### FAISS for Knowledge Retrieval
FAISS provides millisecond-scale nearest-neighbor search over document embeddings, making RAG feasible within the agent's latency budget.

## Security Decisions
- PII filter (`safety/pii_filter.py`) redacts emails, phone numbers, SSNs, and credit card numbers before any data leaves the system boundary.
- Guardrails (`safety/guardrails.py`) block common prompt injection patterns.
- `.env` is gitignored; `.env.example` documents required keys without exposing values.
