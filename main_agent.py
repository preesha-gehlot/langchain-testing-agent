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



# ===== EXAMPLE USAGE =====
if __name__ == "__main__":
    # initial_state = {
    #     "task": "enhance_collection_with_data",  # Options: "enhance_collection", "enhance_collection_with_data", "create_collection"
    #     "spec_fpath": "downloads/tfl_journey_spec.json",
    #     "api_name": "TFL JourneyResults API",
    #     "existing_collection_fpath": "downloads/initial_postman_collection.json",
    #     "test_data_scenario": "In the TFL JourneyResults endpoint, when the mode is set to an invalid value such as spaceship, the endpoint should return a 400 or 404 response.",
    #     "data_fpath": "./artifacts/lookups_result_1759139776.txt"
    # }
    
    # print("Starting main orchestrator...")
    # print(f"Initial state: {initial_state}\n")
    
    # # Run the main agent
    # result = main_agent.invoke(initial_state)
    
    # print("\n=== Orchestrator Execution Complete ===")
    # print(f"Status: {result['status']}")
    # print(f"Reasoning: {result['reasoning']}")
    # if result.get('generated_collection_fpath'):
    #     print(f"Generated collection saved to: {result['generated_collection_fpath']}")
    # if result.get('data_filepath'):
    #     print(f"Data file generated: ./artifacts/{result['data_filepath']}")
    
    # Optional: Print the graph structure
    # print(f"\nGraph structure: {main_agent.get_graph().draw_ascii()}")
    
    # Generate and save PNG image of the graph
    print("\nGenerating graph visualization...")
    try:
        # Generate PNG image
        png_data = main_agent.get_graph().draw_mermaid_png()
        
        # Save to file
        with open("main_agent_graph.png", "wb") as f:
            f.write(png_data)
        print("Graph PNG saved to: main_agent_graph.png")
        
    except Exception as e:
        print(f"PNG generation failed: {e}")