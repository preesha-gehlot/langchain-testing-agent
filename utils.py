import json 
from logging_utils import setup_logging
from datetime import datetime
from openapi_spec_validator import validate_spec
from typing import List, Optional, Dict, Any
import json

# Configure the module's logger
logger = setup_logging(__name__)

# SPEC VALIDATION UTILITY FUNCTIONS 
def validate_json_spec(spec_path: str) -> Dict:
    spec = None
    try:
        if not spec_path:
            logger.error("No OpenAPI spec URL provided in session state.")
            return {
                "status": "error",
                "message": "No OpenAPI spec URL provided in session state.",
                "validation_status": "failed",
            }
            
        # First validate it's proper JSON
        with open(spec_path, 'r') as f:
            spec_json = json.load(f)
    
        # Validate the OpenAPI spec
        validate_spec(spec_json)
        validation_status = "success"
        validation_result = "valid"
        validation_message = "OpenAPI specification is valid."
        spec = spec_json

    except json.JSONDecodeError as e:
        validation_status =  "error",
        validation_result = "valid"
        validation_message = f"Invalid YAML/JSON format: {e}",
        logger.error(validation_message)
    
    except Exception as e:
        validation_status =  "error",
        validation_result = "valid"
        validation_message = f"OpenAPI specification is invalid: {e}",
        logger.error(validation_message)
    
    validation_json = {
        "status": validation_status, 
        "result": validation_result, 
        "message": validation_message,
        "spec": spec
    }
    
    return validation_json


# CREATE POSTMAN COLLECTION UTILITY FUNCTIONS 
def validate_and_clean_json(response_text):
    """
    Clean and validate the JSON response
    """
    try:
        # Remove any markdown formatting if present
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks if they exist
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]  # Remove ```json
        if cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]   # Remove ```
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]  # Remove trailing ```
        
        cleaned_text = cleaned_text.strip()
        
        # Validate JSON
        collection_json = json.loads(cleaned_text)
        
        logger.info("JSON validation successful")
        return collection_json
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.error(f"Problematic text around position {e.pos}: {response_text[max(0, e.pos-50):e.pos+50]}")
        
        # Try to fix common JSON issues
        return attempt_json_repair(cleaned_text)
    

def attempt_json_repair(text):
    """
    Attempt to repair common JSON formatting issues
    """
    try:
        # Common fixes
        fixes = [
            # Remove trailing commas
            lambda x: x.replace(',}', '}').replace(',]', ']'),
            # Fix unescaped quotes in strings
            lambda x: x.replace('\\"', '"'),
        ]
        
        for fix in fixes:
            try:
                fixed_text = fix(text)
                return json.loads(fixed_text)
            except:
                continue
                
        logger.error("Could not repair JSON")
        return None
        
    except Exception as e:
        logger.error(f"JSON repair failed: {e}")
        return None


# ENHANCE POSTMAN COLLECTION UTILITY FUNCTIONS 
def get_last_test_case_from_collection(collection_path: str):
    """
    Reads the Postman collection JSON file and extracts the last test case.

    Args:
        collection_path (str): Path to the Postman collection JSON file.

    Returns:
        dict: The last test case in the collection.
    """
    try:
        with open(collection_path, 'r') as f:
            collection = json.load(f)

        # Ensure the collection has items
        if 'item' in collection and isinstance(collection['item'], list) and collection['item']:
            return collection['item'][-1]  # Return the last test case
        else:
            raise ValueError("The collection does not contain any test cases.")

    except Exception as e:
        logger.error(f"Failed to read Postman collection: {e}")
        raise


# ENHANCE WITH DATA POSTMAN COLLECTION UTILITY FUNCTIONS
def _extract_rows(res: Any) -> List[Dict[str, Any]]:
    """
    Normalize ADK/MCP tool results into a list[dict] rows.
    Handles:
      - dict with {"response":{"data":[...]}} or {"data":[...]}
      - object with .content = [TextContent(text='{"..."}'), ...]
      - JSON array or newline-delimited JSON inside text blocks
    """
    rows: List[Dict[str, Any]] = []

    # dict payload path
    if isinstance(res, dict):
        payload = res.get("response", res)
        data = payload.get("data")
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
        # fall through to check "content" list, if any
        content = payload.get("content", [])
    else:
        # object-style (what you printed): res.content is a list of TextContent
        content = getattr(res, "content", [])

    for blk in content or []:
        txt = blk.get("text") if isinstance(blk, dict) else getattr(blk, "text", None)
        if not isinstance(txt, str) or not txt.strip():
            continue
        # try: single JSON object or array
        try:
            parsed = json.loads(txt)
            if isinstance(parsed, dict):
                rows.append(parsed)
                continue
            if isinstance(parsed, list):
                rows.extend([r for r in parsed if isinstance(r, dict)])
                continue
        except Exception:
            pass
        # try: newline-delimited JSON
        for line in txt.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
            except Exception:
                continue

    return rows


# SAVING UTILITY FUNCTIONS 
def save_postman_collection_to_file(collection_json, mode) -> str:
    """
    Saves the Postman collection JSON to a file in the current directory.
    
    Args:
        collection_json (dict): The Postman collection JSON object
        tool_context (ToolContext): Provides access to session state for context
    
    Returns:
        str: The file path where the collection was saved
    """
    
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    if mode == "created":
        version = "initial" 
    elif mode == "enhanced": 
        version = "enhanced"
    else:
        version = "enhanced_with_data"
    output_filename = f"{current_time}_{version}_postman_collection.json"
    
    # Save the collection to file
    with open(output_filename, 'w') as f:
        json.dump(collection_json, f, indent=2)
    
    return output_filename


def merge_and_save_postman_collection(existing_collection: dict, new_tests: list, with_data: bool = False) -> dict:
    """
    Merge new test cases into an existing Postman collection and save to file.
    
    Args:
        existing_collection (dict): The full existing Postman collection JSON
        new_tests (list): Array of new test case objects to add
        output_folder (str): Folder path where the merged collection will be saved
        filename (str): Name of the output file (default: "enhanced_collection.json")
    
    Returns:
        dict: Status and file path of the saved collection
    """
    try:
        # Create a deep copy to avoid modifying the original
        import copy
        merged_collection = copy.deepcopy(existing_collection)
        
        # Ensure the collection has an 'item' array
        if 'item' not in merged_collection:
            merged_collection['item'] = []
        
        # Add new tests to the existing collection's items
        merged_collection['item'].extend(new_tests)
        
        # Update collection info if needed
        if 'info' in merged_collection and 'name' in merged_collection['info']:
            # Optionally update the name to indicate it's enhanced
            original_name = merged_collection['info']['name']
            if not original_name.endswith(' (Enhanced)'):
                merged_collection['info']['name'] = f"{original_name} (Enhanced)"
        
        if with_data: 
            filepath = save_postman_collection_to_file(merged_collection, "enhanced with data")
        else: 
            filepath = save_postman_collection_to_file(merged_collection, "enhanced")
        
        logger.info(f"Enhanced Postman collection saved to: {filepath}")
        
        return {
            "status": "success",
            "message": f"Collection enhanced with {len(new_tests)} new test cases",
            "file_path": filepath,
            "test_count": len(merged_collection.get('item', []))
        }
        
    except Exception as e:
        error_message = f"Failed to merge and save Postman collection: {str(e)}"
        logger.error(error_message)
        return {
            "status": "error",
            "message": error_message,
            "file_path": None
        }

