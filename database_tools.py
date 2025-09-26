# simple_mcp_tool.py
import asyncio
import time
import aiohttp
import json
from typing import Dict, Any
from typing_extensions import Annotated
from utils import _extract_rows
from logging_utils import setup_logging
# LangChain imports
from langchain.tools import BaseTool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field


tools_logger = setup_logging(__name__)

class BaseMCPTool(BaseTool):
    """Base class for all MCP tools with common functionality"""
    
    # Define the URL as a class variable that can be overridden
    mcp_url: str = "https://mcp-toolbox-339727264964.europe-west2.run.app/mcp"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def _call_mcp_tool(self, tool_name: str, arguments: dict = None) -> Dict[str, Any]:
        """Call MCP tool using proper MCP protocol"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.mcp_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        return {"error": f"HTTP {response.status}: {error_text}"}
                    
                    result = await response.json()
                    
                    if "error" in result:
                        return {"error": result["error"]["message"]}
                    
                    if "result" in result:
                        return {"success": True, "data": result["result"]}
                    
                    return {"success": True, "data": result}
                    
            except Exception as e:
                return {"error": f"Request failed: {str(e)}"}
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """Sync wrapper for async method"""
        return asyncio.run(self._arun(**kwargs))

# Input schema for the tool
class ListTablesInput(BaseModel):
    pass

class ListTablesTool(BaseMCPTool):
    name: str = "list_tables"
    description: str = """
    Get all the tables that exist in the database
    Returns:
        A dict with:
          - status: "success" | "error"
          - tables: list of the tables and a description of what each table stores in the database. 
    """
    args_schema: type[BaseModel] = ListTablesInput
    
    async def _arun(self, **kwargs) -> Dict[str, Any]:
        """Call the list-tables tool on MCP server"""
        tools_logger.info("Calling list-tables via MCP protocol")
        
        result = await self._call_mcp_tool("list-tables", {})
        
        if "error" in result:
            tools_logger.error(f"MCP call failed: {result['error']}")
            return {"status": "error", "message": result["error"]}
        
        # Extract table information from MCP response
        data = result.get("data", {})
        
        # Handle MCP content format with nested JSON strings
        if isinstance(data, dict) and "content" in data:
            tables = []
            for item in data["content"]:
                if item.get("type") == "text":
                    try:
                        # Parse the JSON string inside the text field
                        table_info = json.loads(item["text"])
                        table_name = table_info.get("TABLE_NAME")
                        table_comment = table_info.get("TABLE_COMMENT", "")
                        
                        if table_name:
                            tables.append((table_name, table_comment))
                    except json.JSONDecodeError as e:
                        tools_logger.warning(f"Failed to parse table JSON: {e}")
                        continue
            
            tools_logger.info(f"Found {len(tables)} tables")
            return {"status": "success", "tables": tables}
        
        else:
            return {"status": "success", "raw_data": data}


class DescribeTableInput(BaseModel):
    table_name: str = Field(description="Name of the table you want to get the schema for in a database.")

class DescribeTableTool(BaseMCPTool):
    name: str = "describe_table"
    description: str = """
    Get the schema for a table in the database

    Returns:
        A dict with:
          - status: "success" | "error"
          - data: list[dict] of rows (present when status == "success"). 
          Each row represents information about one column in the table. 
          - message: str error details (present when status == "error")
    """
    args_schema: type[BaseModel] = DescribeTableInput

    async def _arun(self, table_name, **kwargs) -> Dict[str, Any]:
        """Call the list-tables tool on MCP server"""
        tools_logger.info("Calling describe table via MCP protocol")
        
        result = await self._call_mcp_tool("describe-table", {"table_name": table_name})

        if "error" in result:
            tools_logger.error(f"MCP call failed: {result['error']}")
            return {"status": "error", "message": result["error"]}
        
        # Extract table information from MCP response
        data = result.get("data", {})
        rows = _extract_rows(data)

        return {"status": "success", "data": rows}

class ExecuteSQLInput(BaseModel):
    query: str = Field(description="SQL query that you want to execute on the database")

class ExecuteSQLTool(BaseMCPTool):
    name: str = "execute_sql"
    description: str = """
    Execute an SQL query on the database

    Returns:
        A dict with:
          - status: "success" | "error"
          - data: list[dict] of rows (present when status == "success"). 
          Each row represents one row in the SQL query result. 
          - message: str error details (present when status == "error")
    """
    args_schema: type[BaseModel] = DescribeTableInput

    async def _arun(self, query, **kwargs) -> Dict[str, Any]:
        """Call the list-tables tool on MCP server"""
        tools_logger.info("Calling describe table via MCP protocol")
        
        result = await self._call_mcp_tool("execute-sql", {"sql": query})

        if "error" in result:
            tools_logger.error(f"MCP call failed: {result['error']}")
            return {"status": "error", "message": result["error"]}
        
        # Extract table information from MCP response
        data = result.get("data", {})
        rows = _extract_rows(data)

        return {"status": "success", "data": rows}


# Create the tool instance
list_tables_tool = ListTablesTool()
describe_table_tool = DescribeTableTool()
execute_sql_tool = ExecuteSQLTool()
