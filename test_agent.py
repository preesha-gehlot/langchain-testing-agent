import requests
import json
# In the TFL JourneyResults endpoint, when the mode is set to an invalid value such as spaceship, the endpoint should return a 400 or 404 response.
# In the TFL JourneyResults endpoint, if the journey is from a station in London that accepts oyster cards to a station in London that does not accept oyster cards, when the mode is set to tube, the endpoint should return a 400 response.

# ===== EXAMPLE USAGE =====
if __name__ == "__main__":

    test_data = {
        "issueKey": 'TDT-1',
        "apiName": 'TFL Journey Results API',
        "postmanAction": 'Enhance Test Collection With Data',
        "summary": 'Update tfl API',
        "description": 'No description',
        "openapi_spec": {
            "id": '10016',
            "filename": 'tfl_journey_spec.json',
            "contentUrl": 'https://api.atlassian.com/ex/jira/282ca0ed-32f3-40be-9e3c-abc56ad6bde5/rest/api/3/attachment/content/10016'
        },
        "postman_collection": {
            "id": '10015',
            "filename": 'initial_postman_collection.json',
            "contentUrl": 'https://api.atlassian.com/ex/jira/282ca0ed-32f3-40be-9e3c-abc56ad6bde5/rest/api/3/attachment/content/10015'
        },
        "user_req": {
            "id": '10132',
            "filename": 'user_req_oyster.txt',
            "contentUrl": 'https://api.atlassian.com/ex/jira/282ca0ed-32f3-40be-9e3c-abc56ad6bde5/rest/api/3/attachment/content/10132'
        }
    }
    
    try:
        url = "http://127.0.0.1:8000/run-testing-agent/"
        # Add timeout for better error handling with remote endpoints
        response = requests.post(url, json=test_data, timeout=600)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server at http://127.0.0.1:8000")
        print("Make sure the FastAPI server is running with: uvicorn main:app --reload")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    

  