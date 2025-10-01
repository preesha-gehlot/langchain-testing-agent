import json
import os
from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from states import AgentState
from utils import get_last_test_case_from_collection, merge_and_save_postman_collection
from typing_extensions import Literal
from langgraph.types import Command
from langgraph.graph import END
from prompts import generate_data_test_cases_sys_prompt
from datetime import datetime
from logging_utils import setup_logging

tools_logger = setup_logging(__name__)

def generate_new_postman_tests_with_data(state: AgentState) -> Command[Literal["upload_to_gcp_bucket", "__end__"]]:
    # Load output schema from file
    tools_logger.info("generating new postman tests based on data")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, 'response_schemas', 'response_schema_enhance.json')
    tools_logger.info(f"Loading Postman test case schema from: {schema_path}")
    with open(schema_path, 'r') as f:
        POSTMAN_TEST_CASE_SCHEMA = json.load(f)

    # Get openapi spec
    spec_path = state["spec_fpath"]
    with open(spec_path, 'r') as f:
        openapi_spec = json.load(f)
    openapi_spec_doc = json.dumps(openapi_spec, indent=2)

    # Get existing collection and one example of postman test
    collection_path = state["existing_collection_fpath"]
    with open(collection_path, 'r') as f:
        current_tests = json.load(f)
    test_case = get_last_test_case_from_collection(collection_path)
    test_case_str = json.dumps(test_case, indent=2)

    # Get the test data 
    user_requirement = state["test_data_scenario"]

    test_data_path = state["data_fpath"]
    with open(test_data_path, 'r') as f:
        data_content = f.read()

    # Create the prompt
    prompt = generate_data_test_cases_sys_prompt.format(
        test_case_str=test_case_str,
        openapi_spec_doc=openapi_spec_doc,
        user_requirement=user_requirement,
        data_content=data_content
    )
    tools_logger.info("calling gpt to generate new test cases based on the data")

    model = init_chat_model(
        model="gpt-4o",
        model_provider="openai", 
        temperature=0.0
    )
    
    # Create a model with JSON schema structured output
    structured_model = model.with_structured_output(
        schema=POSTMAN_TEST_CASE_SCHEMA,
        method="json_schema",
        strict=True
    )
    
    # Use LangChain to call the model
    postman_collection_object = structured_model.invoke([
        SystemMessage(content=prompt),
    ])

    # Extract test cases from the structured response
    new_collection_list = postman_collection_object["test_cases"]
    
    output = merge_and_save_postman_collection(current_tests, new_collection_list, True)

    if output["status"] != "success":
        return Command(
            goto=END,
            update={
                "status": "error",
                "reasoning": f"Failed to save enhanced Postman collection: {output.get('message', 'Unknown error')}"
            }
        )
    else:
        return Command(
            goto="upload_to_gcp_bucket",
            update={
                "generated_collection_fpath": output["file_path"]
            }
        )
