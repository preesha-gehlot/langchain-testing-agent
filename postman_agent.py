import json
from dotenv import load_dotenv
load_dotenv()

import os
from google.cloud import storage
from states import AgentState
from utils import validate_json_spec
from typing_extensions import Literal
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from create_collection import generate_new_postman_collection
from enhance_with_data_collection import generate_new_postman_tests_with_data
from enhance_collection import enhance_postman_collection
from logging_utils import setup_logging

# Get a logger for this tools module using our improved setup
tools_logger = setup_logging(__name__)

def validate_openapi_spec(state: AgentState) -> Command[Literal["generate_new_postman_tests_with_data", "generate_new_postman_collection", "enhance_postman_collection", "__end__"]]:
    """
    Validates an OpenAPI specification file.
    
    Args:
        spec_path: Path or URL to the OpenAPI specification file to validate
        
    Returns:
        Dict containing validation status and results
    """
    spec_path = state["spec_fpath"]
    tools_logger.info(f"Validating OpenAPI spec at: {spec_path}")
    
    
    validation_json = validate_json_spec(spec_path)
    
    if validation_json["status"] == "success":
        tools_logger.info(f"OpenAPI spec from {spec_path} is valid.")
        if state["task"] == "create_collection":
            return Command(
                goto="generate_new_postman_collection"
            )
        elif state["task"] == "enhance_collection_with_data": 
            return Command(
                goto="generate_new_postman_tests_with_data"
            )
        elif state["task"] == "enhance_collection":
            return Command(
                goto="enhance_postman_collection"
            )
        else:
            return Command(
                goto=END,
                update={
                    "status": "error",
                    "reasoning": f"Unknown task: {state['task']}"
                }
            )
    else:
        tools_logger.warning(f"OpenAPI spec validation failed: {validation_json}")
        return Command(
            goto=END,
            update={
                "status": "error",
                "reasoning": f"OpenAPI spec validation failed: {validation_json}"
            }
        )
      

def upload_to_gcp_bucket(state: AgentState):
    """
    Uploads a file to a Google Cloud Storage bucket.
    
    Args:
        file_path: Local path to the file to upload
        api_name: Name of the API (used as folder name in bucket)
        bucket_name: GCS bucket name (optional, will use GCS_BUCKET_NAME env var if not provided)
        
    Returns:
        Dict containing upload status and messages
    """
    file_path = state["generated_collection_fpath"]
    api_name = state["api_name"]
    
    try:
        # Initialize the client
        client = storage.Client()
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        
        bucket = client.bucket(bucket_name)
        file_name = os.path.basename(file_path)
        
        # Create the blob path with api_name as folder
        blob_path = f"{api_name}/{file_name}"
        blob = bucket.blob(blob_path)
        
        # Upload the file
        blob.upload_from_filename(file_path, content_type='application/json')
        tools_logger.info(f"File uploaded to GCS: gs://{bucket_name}/{blob_path}")
        
        return {
            "status": "success",
            "reasoning": f"New postman collection uploaded successfully to gs://{bucket_name}/{blob_path}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "reasoning": f"Upload failed: {str(e)}"
        }

# ===== AGENT NODES =====
postman_agent_builder = StateGraph(AgentState)
# Add nodes to the graph
postman_agent_builder.add_node("validate_openapi_spec", validate_openapi_spec)
postman_agent_builder.add_node("generate_new_postman_tests_with_data", generate_new_postman_tests_with_data)
postman_agent_builder.add_node("generate_new_postman_collection", generate_new_postman_collection)
postman_agent_builder.add_node("enhance_postman_collection", enhance_postman_collection)
postman_agent_builder.add_node("upload_to_gcp_bucket", upload_to_gcp_bucket)

# Add edges to connect nodes
postman_agent_builder.add_edge(START, "validate_openapi_spec")
postman_agent_builder.add_edge("upload_to_gcp_bucket", END)
postman_agent = postman_agent_builder.compile()