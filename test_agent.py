import requests
import json
# In the TFL JourneyResults endpoint, when the mode is set to an invalid value such as spaceship, the endpoint should return a 400 or 404 response.


# ===== EXAMPLE USAGE =====
if __name__ == "__main__":
    initial_state = {
        "task": "enhance_collection_with_data",  # Options: "enhance_collection", "enhance_collection_with_data", "create_collection"
        "spec_fpath": "downloads/tfl_journey_spec.json",
        "api_name": "TFL JourneyResults API",
        "existing_collection_fpath": "downloads/initial_postman_collection.json",
        "test_data_scenario": "In the TFL JourneyResults endpoint, if the journey is from a station in London that accepts oyster cards to a station in London that does not accept oyster cards, when the mode is set to tube, the endpoint should return a 400 response."
    }
    
    print("Starting main orchestrator via HTTP request...")
    print(f"Initial state: {initial_state}\n")
    
    # Send HTTP POST request to the FastAPI server
    try:
        url = "http://127.0.0.1:8000/run-testing-agent/"
        headers = {"Content-Type": "application/json"}
        
        print(f"Sending POST request to: {url}")
        response = requests.post(url, json=initial_state, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("\n=== Orchestrator Execution Complete ===")
            print(f"Status: {result['status']}")
            print(f"Reasoning: {result['reasoning']}")
            if result.get('generated_collection_fpath'):
                print(f"Generated collection saved to: {result['generated_collection_fpath']}")
            if result.get('data_filepath'):
                print(f"Data file generated: ./artifacts/{result['data_filepath']}")
        else:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server at http://127.0.0.1:8000")
        print("Make sure the FastAPI server is running with: uvicorn main:app --reload")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    