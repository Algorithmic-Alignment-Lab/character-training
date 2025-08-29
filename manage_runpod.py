import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def list_runpod_endpoints():
    """
    Lists all serverless endpoints for the authenticated user.
    """
    api_key = os.environ.get("RUNPOD_API_KEY")
    if not api_key:
        print("❌ RUNPOD_API_KEY environment variable not set.")
        return

    print("--- Fetching RunPod Serverless Endpoints ---")
    
    # Based on RunPod API documentation, the correct endpoint is /endpoints
    url = "https://api.runpod.ai/v2/endpoints"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        endpoints = data.get('endpoints', [])
        
        if endpoints:
            print(f"✅ Found {len(endpoints)} endpoint(s):")
            for endpoint in endpoints:
                # Print a summary of each endpoint
                print("\n----------------------------------------")
                print(f"  ID: {endpoint.get('id')}")
                print(f"  Name: {endpoint.get('name')}")
                print(f"  GPUs: {endpoint.get('gpus')}")
                print(f"  Template ID: {endpoint.get('templateId')}")
                print(f"  Workers (Min/Max): {endpoint.get('workersMin')} / {endpoint.get('workersMax')}")
                print("----------------------------------------")
        else:
            print("ℹ️ No serverless endpoints found.")

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
        print("Please ensure your RUNPOD_API_KEY is correct and has the necessary permissions.")
    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred while making the request: {e}")
    except json.JSONDecodeError:
        print("❌ Failed to decode the JSON response from the server.")


def list_runpod_gpus():
    """
    Lists all available GPU types on RunPod.
    """
    api_key = os.environ.get("RUNPOD_API_KEY")
    if not api_key:
        # This is already checked in the other function, but good practice.
        return

    print("\n--- Fetching RunPod GPU Types ---")
    url = "https://api.runpod.ai/v2/gpus"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        gpus = response.json()
        
        if gpus:
            print(f"✅ Found {len(gpus)} GPU types.")
            # Print a few examples
            for gpu in gpus[:3]:
                print(f"  - ID: {gpu.get('id')}, Display Name: {gpu.get('displayName')}")
        else:
            print("ℹ️ No GPU types found.")

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error while fetching GPUs: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"❌ An error occurred while fetching GPUs: {e}")


def explain_deployment():
    """
    Explains how one might deploy an autoscaling pipeline.
    """
    print("\n--- Deploying an Autoscaling Pipeline via API ---")
    print("Yes, it is possible to programmatically create, manage, and deploy autoscaling serverless endpoints using the RunPod API and your API key.")
    print("\nThis is typically done by sending a POST request to the `https://api.runpod.ai/v2/endpoints` endpoint.")
    print("The request body would need to contain a detailed JSON configuration for the new endpoint, specifying parameters such as:")
    print("- `name`: A unique name for your endpoint.")
    print("- `templateId`: The ID of a pre-configured template, which defines the container image, environment variables, etc.")
    print("- `gpus`: The type of GPU to use (e.g., 'NVIDIA GeForce RTX 3090').")
    print("- `workersMin` and `workersMax`: To define the autoscaling range.")
    print("- `idleTimeout`: The time in minutes before a worker is shut down.")
    
    print("\nThis allows for a fully automated CI/CD workflow for your AI models, a practice known as MLOps.")
    print("For detailed instructions and the exact schema for the request, you should consult the official RunPod API documentation.")


if __name__ == "__main__":
    list_runpod_endpoints()
    list_runpod_gpus()
    explain_deployment()
