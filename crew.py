import json
from crewai import Crew, Process
from crew_agents.agents import (
    fraud_detection_agent,
    monitor_agent,
    analyst_agent,
    risk_score_agent,
)
from tasks.tasks import create_tasks


def build_crew(transaction_json: dict) -> Crew:
    tx_str = json.dumps(transaction_json, indent=2)
    anomaly_task, history_task, risk_task, final_task = create_tasks(tx_str)

    return Crew(
        agents=[monitor_agent, analyst_agent, risk_score_agent, fraud_detection_agent],
        tasks=[anomaly_task, history_task, risk_task, final_task],
        process=Process.sequential,
        verbose=True,
    )
