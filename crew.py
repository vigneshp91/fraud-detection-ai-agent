import json
from crewai import  Task, Crew, Process
from agents import fraud_analyst 
from tasks import risk_scoring_task

def build_crew(transaction_json: dict) -> Crew:
    
    crew = Crew(
        agents=[fraud_analyst],
        tasks=[risk_scoring_task],
        process=Process.sequential,
        verbose=True,
    )

    # Inject the transaction into the task at runtime
    risk_scoring_task.description = risk_scoring_task.description.format(
        transaction=json.dumps(transaction_json, indent=2)
    )

    return crew
