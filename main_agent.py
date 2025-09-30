from postman_agent import postman_agent
from test_data_agent import test_data_agent
from states import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing_extensions import Literal
from logging_utils import setup_logging

logger = setup_logging(__name__)

def decide_workflow(state: AgentState) -> Command[Literal["test_data_agent", "postman_agent"]]:
    """
    Decides whether to run test data agent first or go directly to postman agent
    based on the task type.
    """
    task = state.get("task", "")
    
    if task == "enhance_collection_with_data":
        logger.info("Task requires data enhancement - routing to test_data_agent first")
        return Command(goto="test_data_agent")
    else:
        logger.info("Task does not require data enhancement - routing directly to postman_agent")
        return Command(goto="postman_agent")

def run_test_data_agent(state: AgentState):
    """
    Wrapper node to run the test data agent and return its results
    """
    logger.info("Running test data agent...")
    result = test_data_agent.invoke(state)
    logger.info(f"Test data agent completed. Data file: {result.get('data_filepath', 'N/A')}")
    return result

def run_postman_agent(state: AgentState):
    """
    Wrapper node to run the postman agent and return its results
    """
    logger.info("Running postman agent...")
    result = postman_agent.invoke(state)
    logger.info(f"Postman agent completed. Status: {result.get('status', 'N/A')}")
    return result

# ===== MAIN ORCHESTRATOR GRAPH =====
main_graph_builder = StateGraph(AgentState)

# Add nodes
main_graph_builder.add_node("decide_workflow", decide_workflow)
main_graph_builder.add_node("test_data_agent", run_test_data_agent)
main_graph_builder.add_node("postman_agent", run_postman_agent)

# Add edges
main_graph_builder.add_edge(START, "decide_workflow")
main_graph_builder.add_edge("test_data_agent", "postman_agent")  # After test data, always go to postman
main_graph_builder.add_edge("postman_agent", END)

# Compile the main agent
main_agent = main_graph_builder.compile()
