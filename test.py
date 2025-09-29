from postman_agent import postman_agent
# "In the TFL JourneyResults endpoint, if the journey is from a station in London that accepts oyster cards to a station in London that does not accept oyster cards, when the mode parameter is set to tube, the endpoint should return a 400 response.",
    
initial_state = {
    "task": "enhance_collection", # or "enhance_collection_with_data"
    "spec_fpath": "downloads/tfl_journey_spec.json",
    "api_name": "TFL JourneyResults API",
    "existing_collection_fpath": "downloads/initial_postman_collection.json",
    "test_data_scenario": "In the TFL JourneyResults endpoint, when the mode is set to an invalid value such as spaceship, the endpoint should return a 400 or 404 response. ",
    "data_fpath": "./artifacts/lookups_result_1759139776.txt"
}
    
print("Starting agent execution...")
print(f"Initial state: {initial_state}\n")

# Run the agent synchronously
result = postman_agent.invoke(initial_state)

print("\n=== Agent Execution Complete ===")
print(f"Status: {result['status']}")
print(f"Reasoning: {result['reasoning']}")
if result.get('generated_collection_fpath'):
    print(f"Generated collection saved to: {result['generated_collection_fpath']}")