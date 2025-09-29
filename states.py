"""
State definitions and pydantic schemas for gathering lookup requirements from our database. 
"""

import operator
from typing_extensions import TypedDict, Optional, List, Dict, Tuple
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    """Input state for the full agent"""
    task: str  # "create_collection" or "enhance_collection_with_data"
    spec_fpath: str
    api_name: str
    existing_collection_fpath: Optional[str]  # Path to existing Postman collection JSON file
    test_data_scenario: str
    lookup_requests: Optional[List[str]] = None
    tables: Optional[List[Tuple[str, str]]] = None
    data_fpath: Optional[str]  # Path to file with test data
    generated_collection_fpath: Optional[str]  # Path to save generated Postman collection JSON file
    status: Optional[str] = None
    reasoning: Optional[str] = None

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

class PlannedTestCases(BaseModel):
    """Schema for planned test cases generation"""
    test_cases: List[str] = Field(
        description="A list of planned test cases to be executed"
    )