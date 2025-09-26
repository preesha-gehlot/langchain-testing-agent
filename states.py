"""
State definitions and pydantic schemas for gathering lookup requirements from our database. 
"""

import operator
from typing_extensions import TypedDict, Optional, List, Dict, Tuple
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    """Input state for the full agent"""
    test_data_scenario: str
    lookup_requests: Optional[List[str]] = None
    tables: Optional[List[Tuple[str, str]]] = None

class DataSearchState(MessagesState):
    """Input state for the data search agent."""
    lookup_query: str
    all_tables: List[Tuple[str, str]]
    status: str = "searching"
    reasoning: str = ""
    last_query_result: Optional[Dict] = None


# ==== STRUCTURED OUTPUT SCHEMAS ====
class GetRequirements(BaseModel):
    """Schema for lookup requests generation"""
    data_to_lookup: List[str] = Field(
        description="A list of lookup requests to be executed on the database"
    )