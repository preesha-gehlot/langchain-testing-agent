from dotenv import load_dotenv
load_dotenv()

from states import DataSearchState
from prompts import data_search_agent_prompt
from database_tools import describe_table_tool, execute_sql_tool, mark_complete_tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from typing import List, Tuple
from typing_extensions import Literal
from logging_utils import setup_logging

logger = setup_logging(__name__)

# ===== CONFIGURATION =====
tools = [describe_table_tool, execute_sql_tool, mark_complete_tool]
tools_by_name = {tool.name: tool for tool in tools}
# Initialize model
model = init_chat_model(
    model="gpt-4o",
    model_provider="openai", 
    temperature=0.0
)
model_with_tools = model.bind_tools(tools, tool_choice="auto", parallel_tool_calls=False)

# ===== UTILS =====

def format_tables(tables: List[Tuple[str, str]]) -> str:
    return "\n".join([f"- {name}: {desc}" for name, desc in tables])

# ===== WORKFLOW NODES =====

def llm_call(state: DataSearchState):
    tables = format_tables(state["all_tables"])
    final_prompt = data_search_agent_prompt.format(lookup_query=state["lookup_query"], all_tables_formatted=tables)
    response = model_with_tools.invoke(
        [SystemMessage(content=final_prompt), *state["messages"]]
    )

    return {"messages": response}

def tool_node(state: DataSearchState) -> Command[Literal["llm_call", "__end__"]]:
    last_message = state["messages"][-1]
    
    tool_call = last_message.tool_calls[0]  # Assume single tool call for simplicity
    logger.info(f"Tool call: {tool_call}")
    observation = None
    tool_name = tool_call["name"]
    args = tool_call["args"]

    # assume if LLM calls mark complete that is the only tool it calls 
    if tool_name == "mark_complete":
        logger.info("Calling mark complete tool")
        status = args["status"]
        reasoning = args["reasoning"]

        return Command(
            goto=END, 
            update={
                "status": status,
                "reasoning" : reasoning,
            }    
        )

    tool = tools_by_name[tool_name]
    observation= tool.invoke(tool_call["args"])
    tool_output = ToolMessage(
        content=str(observation),
        name= tool_name,
        tool_call_id = tool_call["id"]
    )

    if tool_name == "describe_table":
        return Command(
            goto="llm_call",
            update={
                "messages": [tool_output],
                "last_query_result" : {
                    "tool_name": tool_name,
                    "status": observation["status"],
                    "table": args["table_name"],
                    "data": observation["data"]
                }
            }
        ) 
    elif tool_name == "execute_sql":
        return Command(
            goto="llm_call",
            update={
                "messages": [tool_output],
                "last_query_result" : {
                    "tool_name": tool_name,
                    "status": observation["status"],
                    "query": args["query"],
                    "data": observation["data"]
                }
            }
        )


# ===== AGENT NODES =====
data_agent_builder = StateGraph(DataSearchState)
# Add nodes to the graph
data_agent_builder.add_node("llm_call", llm_call)
data_agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
data_agent_builder.add_edge(START, "llm_call")
data_agent_builder.add_edge("llm_call", "tool_node")
data_search_agent = data_agent_builder.compile()


