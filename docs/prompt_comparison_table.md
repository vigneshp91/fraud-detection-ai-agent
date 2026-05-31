# Prompt Comparison Table

| Dimension | Zero-shot | Few-shot | Chain-of-Thought | Structured Output (used) |
|---|---|---|---|---|
| **Format compliance** | Low | Medium | Medium | High |
| **Reasoning visibility** | Low | Medium | High | High |
| **Consistency** | Low | Medium | Medium | High |
| **Ease of parsing** | Low | Medium | Low | High |
| **Token cost** | Low | Medium | High | Medium |

## Decision
Structured output prompting was chosen for the final report task because it guarantees machine-readable JSON, enables direct Pydantic validation, and forces the agent to commit to explicit risk factors and a recommendation.

Chain-of-thought was retained in intermediate tasks (anomaly detection, history analysis, risk scoring) to preserve reasoning transparency before the final synthesis step.
