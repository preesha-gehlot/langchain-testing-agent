from utils import merge_and_save_postman_collection, get_last_test_case_from_collection
from logging_utils import setup_logging
import json
import os
from states import AgentState, PlannedTestCases
from langchain.chat_models import init_chat_model
from prompts import plan_functional_test_cases_sys_prompt, functional_test_case_generation_sys_prompt
from langchain_core.messages import SystemMessage 
from typing_extensions import Literal
from langgraph.types import Command
from langgraph.graph import END


# Get a logger for this tools module using our improved setup
tools_logger = setup_logging(__name__)

model = init_chat_model(
    model="gpt-4o",
    model_provider="openai", 
    temperature=0.0
)


def define_new_tests(openapi_spec_doc, postman_collection, user_requirement):
    """
    Identify new test cases to add to an existing Postman collection based on user requirements.

    Args:
        client: OpenAI client instance for making API calls.
        openapi_spec_doc (str): JSON string of the OpenAPI specification.
        postman_collection (str): JSON string of the existing Postman collection.
        user_requirement (str): User requirements as a string.

    Returns:
        str: Bullet point list of new test case descriptions, or an empty string if no new tests are needed.
    """

    structured_output_model = model.with_structured_output(PlannedTestCases)

    system_prompt = plan_functional_test_cases_sys_prompt.format(
        openapi_spec_doc=openapi_spec_doc,
        postman_collection=postman_collection,
        user_requirement=user_requirement
    )

    response = structured_output_model.invoke([
        SystemMessage(content=system_prompt)
    ])

    return response.test_cases



def generate_new_postman_tests(collection_path, openapi_spec_doc, new_tests):
    """
    Generate new Postman test cases based on test case descriptions and OpenAPI spec.

    Args:
        collection_path (str): Path to the existing Postman collection JSON file.
        openapi_spec_doc (str): JSON string of the OpenAPI specification.
        new_tests (str): Bullet point list of new test case descriptions.

    Returns:
        list: List of new Postman test case objects.
    """
    # Load output schema     
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, 'response_schemas', 'response_schema_enhance.json')
    tools_logger.info(f"Loading Postman test case schema from: {schema_path}")
    with open(schema_path, 'r') as f:
        POSTMAN_TEST_CASE_SCHEMA = json.load(f)

    test_case = get_last_test_case_from_collection(collection_path)
    test_case_str = json.dumps(test_case, indent=2)

    structured_model = model.with_structured_output(
        schema=POSTMAN_TEST_CASE_SCHEMA,
        method="json_schema",
        strict=True
    )

    system_prompt = functional_test_case_generation_sys_prompt.format(
        test_case_str=test_case_str,
        openapi_spec_doc=openapi_spec_doc,
        new_tests="\n".join(new_tests)
    )

    postman_collection_object = structured_model.invoke([
        SystemMessage(content=system_prompt),
    ])

    new_collection_list = postman_collection_object["test_cases"]
    
    return new_collection_list



def enhance_postman_collection(state: AgentState) -> Command[Literal["upload_to_gcp_bucket", "__end__"]]:
    """
    Enhance an existing Postman collection by adding new test cases based on user requirements.

    Args:
        tool_context (ToolContext): Context object containing paths to spec, collection, and user requirements.

    Returns:
        dict: Status and message about the enhancement process.
    """

    # Convert OpenAPI spec to JSON string
    spec_path = state["spec_fpath"]
    with open(spec_path, 'r') as f:
        openapi_spec = json.load(f)
    openapi_spec_doc = json.dumps(openapi_spec, indent=2)

    # Get existing postman collection
    collection_path = state["existing_collection_fpath"]
    with open(collection_path, 'r') as f:
        current_tests = json.load(f)
    postman_collection = json.dumps(current_tests, indent=2)

    # Get user requirements 
    user_req = state["test_data_scenario"]

    try:
        new_tests = define_new_tests(openapi_spec_doc, postman_collection, user_req)
        tools_logger.info(f"Planned new test cases: {new_tests}")

    except Exception as e:
        return Command(
            goto=END,
            update={
                "status": "error",
                "reasoning": f"An unexpected error occurred during OpenAI API call: {e}"
            }
        )

    if new_tests:
        try: 
            new_collection_list = generate_new_postman_tests(collection_path, openapi_spec_doc, new_tests)

        except Exception as e:
            return Command(
                goto=END,
                update={
                    "status": "error",
                    "reasoning": f"An unexpected error occurred during OpenAI API call: {e}"
                }
            )     
        
        output = merge_and_save_postman_collection(current_tests, new_collection_list)

        return Command(
            goto="upload_to_gcp_bucket",
            update={
                "status": "success",
                "reasoning": "Collection enhanced with new test cases.",
                "generated_collection_fpath": output.get("file_path", ""),
            }
        )
    
    else:
        return Command(
            goto=END,
            update={
                "status": "success",
                "reasoning": "No new test cases needed based on the user requirements."
            }
        )
