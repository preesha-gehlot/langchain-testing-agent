from fastapi import FastAPI
from main_agent import main_agent

app = FastAPI()

@app.post("/run-testing-agent/")
def run_testing_agent(state: dict):
    result = main_agent.invoke(state)
    return result