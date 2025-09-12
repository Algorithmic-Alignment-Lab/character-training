import os
import runpod
from dotenv import load_dotenv
import json

def list_all_endpoints():
    """
    Initializes the RunPod SDK, fetches all endpoints, and prints their details.
    """
    # --- Load API Key ---
    load_dotenv()
    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        print("❌ RUNPOD_API_KEY environment variable not set.")
        return
    
    runpod.api_key = api_key
    print("✅ RUNPOD_API_KEY loaded. Fetching endpoints...")

    try:
        endpoints = runpod.get_endpoints()
        
        if not endpoints:
            print("\nℹ️ No endpoints found on your account.")
            return

        print(f"\n--- Found {len(endpoints)} Endpoint(s) ---")
        for endpoint in endpoints:
            print("\n----------------------------------------")
            print(f"  Name:           {endpoint.get('name')}")
            print(f"  ID:             {endpoint.get('id')}")
            print(f"  Template ID:    {endpoint.get('templateId')}")
            print(f"  GPU(s):         {endpoint.get('gpuIds')}")
            print(f"  Workers:        {endpoint.get('workersRunning', 0)} running")
            print(f"  Scaling:        Min {endpoint.get('workersMin')} / Max {endpoint.get('workersMax')}")
            print("----------------------------------------")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    list_all_endpoints()
