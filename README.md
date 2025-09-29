# Test case generation agent
This is an initial POC, so this agent only handles unit test cases. 

## Data search agent ([data_agent.py](data_agent.py) and [database_tools.py](database_tools.py))

The data search agent is responsible for intelligently searching and retrieving data from databases to support test case generation. It consists of two main components:

**data_agent.py**: Implements a LangGraph-based agent that uses GPT-4o to orchestrate database operations. The agent takes a lookup query and available database tables, then intelligently decides which database operations to perform. It uses a workflow with two main nodes:
- `llm_call`: Processes the lookup query and decides what database operations to execute
- `tool_node`: Executes database tools and handles the results, updating the agent state accordingly

**database_tools.py**: Provides a suite of database interaction tools that communicate with a remote database via MCP (Model Context Protocol):
- `ListTablesTool`: Retrieves all available tables and their descriptions from the database
- `DescribeTableTool`: Gets the schema information for a specific table
- `ExecuteSQLTool`: Executes SQL queries on the database and returns results
- `MarkCompleteTool`: Marks a data search task as complete with success/failure status

The agent iteratively uses these tools to understand the database structure and find the requested data, marking tasks as complete when data is found or when all options are exhausted.

![Data Search Agent](graphs/data_search_agent.png)

## Test data agent ([test_data_agent.py](test_data_agent.py))

The test data agent orchestrates the process of generating test data for specific test scenarios. It leverages the data search agent to find relevant data from databases and structures it for test case generation.

The agent implements a three-stage workflow:
1. **get_requirements**: Uses GPT-4o-mini with structured output to analyze test scenarios and identify what data needs to be looked up from the database
2. **list_tables**: Retrieves available database tables using the MCP tools to understand what data sources are available
3. **run_lookups**: For each identified data requirement, invokes the data search agent to find and retrieve the actual data from the database

The agent saves all retrieved data to timestamped artifact files, handling both successful lookups and failed attempts. This provides a comprehensive data foundation that can be used by downstream agents for generating realistic test cases with actual database content.

![Test Data Agent](graphs/test_data_agent.png)

## Postman generation agent ([postman_agent.py](postman_agent.py))

The postman generation agent handles the creation and enhancement of Postman collections for API testing. It supports multiple workflows for different testing scenarios:

The agent validates OpenAPI specifications and then routes to different collection generation strategies based on the task:
- **create_collection**: Generates new Postman collections from OpenAPI specs
- **enhance_collection_with_data**: Enhances existing collections by incorporating real test data from databases
- **enhance_collection**: Improves existing collections with better test cases and assertions

Key features include:
- OpenAPI specification validation to ensure API specs are properly formatted
- Integration with Google Cloud Storage for uploading generated collections
- Support for enhancing collections with realistic test data retrieved by the test data agent
- Automatic file management and artifact generation

The agent ensures that generated Postman collections are comprehensive, include realistic test data, and are properly validated before being made available for testing.

![Postman Generation Agent](graphs/postman_generation_agent.png)

## Main agent ([main_agent.py](main_agent.py))

The main agent serves as the orchestrator that coordinates the test data agent and postman generation agent based on the specific testing requirements. It implements intelligent workflow routing to optimize the testing pipeline.

The orchestrator uses a decision-based workflow:
1. **decide_workflow**: Analyzes the task type to determine if data enhancement is needed
   - For `enhance_collection_with_data` tasks: Routes to test data agent first to gather database content
   - For other tasks: Routes directly to postman agent
2. **run_test_data_agent**: Executes the test data agent when real database content is needed for test cases
3. **run_postman_agent**: Executes the postman generation agent to create or enhance API test collections

This architecture ensures efficient resource utilization - the potentially expensive database lookup operations are only performed when test scenarios specifically require real data. The main agent coordinates the entire pipeline, ensuring that data flows correctly between agents and that the final output meets the testing requirements.

![Main Agent](graphs/main_agent.png)

