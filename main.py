from fastapi import FastAPI, HTTPException
from main_agent import main_agent
from pydantic import BaseModel
from pathlib import Path
import aiohttp
import os
import aiofiles
from datetime import datetime
from logging_utils import setup_logging
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logger = setup_logging(__name__)

app = FastAPI()

# Create downloads directory
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Simple models
class Attachment(BaseModel):
    id: str
    filename: str
    contentUrl: str

class IssueRequest(BaseModel):
    issueKey: str
    apiName: str
    postmanAction: str
    summary: str
    description: str
    openapi_spec: Attachment
    postman_collection: Attachment = None
    user_req: Attachment = None

task_mapping = {
    "Enhance Test Collection": "enhance_collection", 
    "Enhance Test Collection With Data": "enhance_collection_with_data",
    "Create Test Collection": "create_collection",
    "Validate OpenAPI spec": "validate_openapi_spec"
    }

# Jira credentials from environment
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")

async def download_file(url: str, filename: str) -> str:
    """Download file from URL and save locally"""
    # Basic auth for Jira
    import base64
    auth = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_TOKEN}".encode()).decode()
    
    headers = {"Authorization": f"Basic {auth}"}
    
    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = DOWNLOAD_DIR / safe_filename
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                logger.error(f"Failed to download: {response.status}")
                raise HTTPException(status_code=400, detail=f"Failed to download: {response.status}")
            
            async with aiofiles.open(file_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)
    return str(file_path)

@app.post("/run-testing-agent/")
async def run_testing_agent(issue: IssueRequest):
    try:
        # Find the first JSON attachment
        spec_attachment = issue.openapi_spec
        collection_attachment = issue.postman_collection or None
        req_attachment = issue.user_req or None
        task = task_mapping[issue.postmanAction]
    
        spec_file_path = await download_file(spec_attachment.contentUrl, spec_attachment.filename)
        collection_file_path = await download_file(collection_attachment.contentUrl, collection_attachment.filename)
        req_file_path = await download_file(req_attachment.contentUrl, req_attachment.filename)
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Issue while downloading files from JIRA {e}" 
        }

    # Read the contents of the requirements file
    try:
        with open(req_file_path, 'r', encoding='utf-8') as f:
            test_data_scenario = f.read()
    except Exception as e:
        logger.error(f"Failed to read requirements file: {e}")
        test_data_scenario = ""

    initial_state = {
        "task": task, 
        "spec_fpath": spec_file_path,
        "api_name": issue.apiName,
        "existing_collection_fpath": collection_file_path,
        "test_data_scenario": test_data_scenario
    }

    print(initial_state)

    result = main_agent.invoke(initial_state)
    return result