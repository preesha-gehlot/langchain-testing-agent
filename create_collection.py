import json
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from states import AgentState
from utils import save_postman_collection_to_file, validate_and_clean_json
from typing_extensions import Literal
from langgraph.types import Command
from langgraph.graph import END
from prompts import generate_postman_collection_sys_prompt
from datetime import datetime
from logging_utils import setup_logging

# Get a logger for this tools module using our improved setup
tools_logger = setup_logging(__name__)

def generate_new_postman_collection(state: AgentState) -> Command[Literal["upload_to_gcp_bucket", "__end__"]]:
    """
    Creates a Postman collection from an OpenAPI specification using Anthropic's Claude model.
    
    Args:
        tool_context: ToolContext object containing the spec path in state
        
    Returns:
        Dict containing the status of collection creation and relevant messages
    """
    tools_logger.info("Creating new Postman collection from OpenAPI spec")
    date = datetime.now().strftime('%m/%d/%Y')

    spec_path = state["spec_fpath"]

    # Read the actual content of the OpenAPI specification file
    with open(spec_path, 'r') as spec_file:
        spec_content = json.load(spec_file)

    # Convert the content to a JSON string
    openapi_spec_doc = json.dumps(spec_content, indent=2)

    system_prompt = generate_postman_collection_sys_prompt.format(
        date=date
    )

    user_prompt = f"""
    OpenAPI specification :
    {openapi_spec_doc}
    """
    
    model = init_chat_model(
        model="claude-sonnet-4-20250514",
        model_provider="anthropic",
        max_tokens=20000,
        temperature=0,  # optional, adjust as needed
    )
    
    # Invoke the model
    response = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    response_text = response.content
    
    tools_logger.info(f"Response received. Total characters: {len(response_text)}")
    # Validate and clean the JSON response
    spec = validate_and_clean_json(response_text)
    
    if spec is None:
        return Command(
            goto=END,
            update={
                "status": "error", 
                "reasoning": "Failed to parse JSON response from Claude"
            }
        )
    
    tools_logger.info("Successfully converted spec to Postman collection with LLM.")
    
    # Save the result to the directory 
    output_filename = save_postman_collection_to_file(spec, "created")
    
    return Command(
        goto="upload_to_gcp_bucket",
        update={
            "generated_collection_fpath": output_filename
        }
    )