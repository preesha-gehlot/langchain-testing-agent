from langchain.tools import tool
from typing import Dict, Optional
import os
from google.cloud import storage
from logging_utils import setup_logging
from utils import validate_json_spec

# Get a logger for this tools module using our improved setup
tools_logger = setup_logging(__name__)


def validate_openapi_spec(spec_path: str) -> Dict:
    """
    Validates an OpenAPI specification file.
    
    Args:
        spec_path: Path or URL to the OpenAPI specification file to validate
        
    Returns:
        Dict containing validation status and results
    """
    tools_logger.info(f"Validating OpenAPI spec at: {spec_path}")
    
    try:
        validation_json = validate_json_spec(spec_path)
        
        if validation_json["status"] == "success":
            tools_logger.info(f"OpenAPI spec from {spec_path} is valid.")
        else:
            tools_logger.warning(f"OpenAPI spec validation failed: {validation_json}")
            
        return validation_json
        
    except Exception as e:
        tools_logger.error(f"Error validating OpenAPI spec: {e}")
        return {
            "status": "error",
            "message": f"Validation failed with error: {str(e)}"
        }


def upload_to_gcp_bucket(file_path: str, api_name: str, bucket_name: Optional[str] = None) -> Dict:
    """
    Uploads a file to a Google Cloud Storage bucket.
    
    Args:
        file_path: Local path to the file to upload
        api_name: Name of the API (used as folder name in bucket)
        bucket_name: GCS bucket name (optional, will use GCS_BUCKET_NAME env var if not provided)
        
    Returns:
        Dict containing upload status and messages
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "message": f"File not found: {file_path}"
        }
    
    try:
        # Initialize the client
        client = storage.Client()
        bucket_name = bucket_name or os.getenv('GCS_BUCKET_NAME')
        
        if not bucket_name:
            return {
                "success": False,
                "message": "No bucket name provided and GCS_BUCKET_NAME environment variable not set"
            }
        
        bucket = client.bucket(bucket_name)
        file_name = os.path.basename(file_path)
        
        # Create the blob path with api_name as folder
        blob_path = f"{api_name}/{file_name}"
        blob = bucket.blob(blob_path)
        
        # Upload the file
        blob.upload_from_filename(file_path, content_type='application/json')
        tools_logger.info(f"File uploaded to GCS: gs://{bucket_name}/{blob_path}")
        
        return {
            "success": True,
            "message": f"File uploaded successfully to gs://{bucket_name}/{blob_path}",
            "gcs_path": f"gs://{bucket_name}/{blob_path}"
        }
        
    except Exception as e:
        tools_logger.error(f"Upload failed: {e}")
        return {
            "success": False,
            "message": f"Upload failed: {str(e)}"
        }

