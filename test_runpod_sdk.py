import os
import runpod
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("--- Testing with runpod SDK ---")

# Get the API key from environment variables
api_key = os.getenv("RUNPOD_API_KEY")

if not api_key:
    print("❌ RUNPOD_API_KEY not found in environment variables.")
else:
    # For security, we won't print the key, but we'll confirm it's loaded.
    print("✅ RUNPOD_API_KEY loaded.")
    
    # Set the API key for the runpod library
    runpod.api_key = api_key

    try:
        # Fetch the endpoints
        print("\nFetching endpoints...")
        endpoints = runpod.get_endpoints()
        
        if endpoints:
            print("✅ Successfully fetched endpoints:")
            for endpoint in endpoints:
                print("\n----------------------------------------")
                print(f"  ID: {endpoint.get('id')}")
                print(f"  Name: {endpoint.get('name')}")
                print(f"  GPUs: {endpoint.get('gpus')}")
                print(f"  Template ID: {endpoint.get('templateId')}")
                print(f"  Workers (Min/Max): {endpoint.get('workersMin')} / {endpoint.get('workersMax')}")
                print("----------------------------------------")
        else:
            print("ℹ️ No endpoints found.")

    except Exception as e:
        print(f"\n❌ An error occurred while using the runpod SDK: {e}")
        print("This might be due to an invalid API key or a network issue.")

