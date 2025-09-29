from dotenv import load_dotenv
load_dotenv()

from states import AgentState, GetRequirements
from prompts import get_requirements_prompt
from database_tools import list_tables_tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from data_agent import data_search_agent
import time 
import os
from logging_utils import setup_logging

model = init_chat_model(
    model="gpt-4o-mini",
    model_provider="openai", 
    temperature=0.0
)

logger = setup_logging(__name__)

# ===== WORKFLOW NODES =====
def get_requirements(state: AgentState):
    #setup structured output model 
    structured_output_model = model.with_structured_output(GetRequirements)

    response = structured_output_model.invoke([
        HumanMessage(content=get_requirements_prompt.format(
            test_data_scenario=state["test_data_scenario"], 
        ))
    ])

    logger.info(response.data_to_lookup)

    return {
        "lookup_requests": response.data_to_lookup
    }

def list_tables(state: AgentState):
    """Node that retrieves available database tables with descriptions using the MCP tool"""
    try:
        # Call the list_tables_tool
        result = list_tables_tool._run()
        
        if result.get("status") == "success":
            # Get tables as list of (name, description) tuples
            tables = result.get("tables", [])
            
            return {
                "tables": tables  # This is already in the format [(name, description), ...]
            }
        else:
            print(f"Error listing tables: {result.get('message', 'Unknown error')}")
            return {
                "tables": []
            }
            
    except Exception as e:
        print(f"Exception while listing tables: {str(e)}")
        return {
            "tables": []
        }

def run_lookups(state:AgentState):
    results_text = []
    failed_lookups = []
    for lookup_query in state["lookup_requests"]:
        initial_state = {
            "messages": [],  # Empty list is fine - no history needed
            "lookup_query": lookup_query,
            "all_tables": state["tables"],
            "status": "searching",
            "reasoning": "",
            "last_query_result": None
        }

        # Invoke the agent
        result = data_search_agent.invoke(initial_state)
        if result["status"] == "found":
            # Format: Query on one line, data below
            results_text.append(f"{lookup_query}:")
            
            # Add the data (assuming it's a list of dicts)
            data = result["last_query_result"]["data"]
            if data:
                for item in data:
                    # Format each data item as a simple string
                    results_text.append(f"  {item}")
            else:
                results_text.append("  No data returned")
            
            results_text.append("")  # Empty line between lookups
            
        else:
            # Track failures separately
            failed_lookups.append(f"{lookup_query}: {result['reasoning']}")
    
    # Combine everything
    final_text = "\n".join(results_text)
    
    if failed_lookups:
        final_text += "\n\nFAILED LOOKUPS:\n"
        final_text += "\n".join(failed_lookups)
    
    filename = f"lookups_result_{int(time.time())}.txt"
    os.makedirs("./artifacts", exist_ok=True)
    
    # Save the file
    with open(f"./artifacts/{filename}", 'w', encoding='utf-8') as f:
        f.write(final_text)

    return {"data_filepath":filename}



# GRAPH CONSTRUCTION
# Nodes
requirements_builder = StateGraph(AgentState)
requirements_builder.add_node("get_requirements", get_requirements)
requirements_builder.add_node("list_tables", list_tables)
requirements_builder.add_node("run_lookups", run_lookups)

# Edges
requirements_builder.add_edge(START, "get_requirements")
requirements_builder.add_edge("get_requirements", "list_tables")
requirements_builder.add_edge("list_tables", "run_lookups")
requirements_builder.add_edge("run_lookups", END)

requirements_sourcing_agent = requirements_builder.compile()