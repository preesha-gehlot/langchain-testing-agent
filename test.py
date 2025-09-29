from requirements_agent import requirements_sourcing_agent
from dotenv import load_dotenv
import os
load_dotenv()

print("Testing Requirements Sourcing Agent")
print("=" * 50)

# Test scenario
test_scenario = """
In the TFL JourneyResults endpoint, if the journey is from a station in London that accepts oyster cards to a station in London that does not accept oyster cards, when the mode parameter is set to tube, the endpoint should return a 400 response.
"""

print(f"Test Scenario: {test_scenario.strip()}")
print("\nRunning agent...")

# Invoke the agent with correct state structure
try:
    result = requirements_sourcing_agent.invoke({
        "test_data_scenario": test_scenario.strip()
    })
    
    print("\nAgent execution completed successfully!")
    print(f"\nGenerated lookup requests: {len(result.get('lookup_requests', []))}")
    for i, lookup in enumerate(result.get('lookup_requests', []), 1):
        print(f"  {i}. {lookup}")
    
except Exception as e:
    print(f"\nError running agent: {e}")
    import traceback
    traceback.print_exc()