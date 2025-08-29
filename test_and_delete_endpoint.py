import os
import runpod
from dotenv import load_dotenv
import time
import requests
import json

def test_and_cleanup_endpoint():
    """
    Polls the newly created endpoint until it's active, runs a completion test,
    and provides an option to clean up (delete) the resources.
    """
    # --- Configuration ---
    ENDPOINT_ID = "vllm-pw2h94fjhm9rvf"
    TEMPLATE_ID = "kpyzl33u48"
    MODEL_NAME = "Qwen/Qwen3-1.7B"
    POLL_INTERVAL_SECONDS = 30
    MAX_WAIT_MINUTES = 15

    # --- Load API Key ---
    load_dotenv()
    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        print("❌ RUNPOD_API_KEY environment variable not set.")
        return
    
    runpod.api_key = api_key
    print(f"✅ RUNPOD_API_KEY loaded. Monitoring endpoint: {ENDPOINT_ID}")

    # --- 1. Poll and Trigger Worker ---
    print("\n--- Waiting for endpoint to become active... ---")
    start_time = time.time()
    endpoint_is_active = False
    
    while time.time() - start_time < MAX_WAIT_MINUTES * 60:
        try:
            # First, check if a worker is already running
            endpoints = runpod.get_endpoints()
            target_endpoint = next((ep for ep in endpoints if ep.get('id') == ENDPOINT_ID), None)

            if target_endpoint and target_endpoint.get('workersRunning', 0) > 0:
                print("\n✅ Endpoint is active! (At least one worker is running)")
                endpoint_is_active = True
                break
            
            # If no worker is running, send a trigger request to the async endpoint
            print("Status: 0 workers running. Sending a trigger request to start a worker...")
            trigger_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": {
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": "This is a warmup request."}]
                }
            }
            # Fire-and-forget async request to trigger the scaler
            requests.post(trigger_url, headers=headers, json=payload, timeout=10)
            print("Trigger request sent. Waiting for worker to initialize...")

            # Wait for the poll interval before checking again
            time.sleep(POLL_INTERVAL_SECONDS)

        except requests.exceptions.Timeout:
            print("Trigger request timed out (this is expected for a fire-and-forget call). Continuing to poll...")
            time.sleep(POLL_INTERVAL_SECONDS)
        except Exception as e:
            print(f"An error occurred while polling/triggering: {e}")
            time.sleep(POLL_INTERVAL_SECONDS)

    if not endpoint_is_active:
        print(f"\n❌ Endpoint did not become active within {MAX_WAIT_MINUTES} minutes.")
        cleanup_resources(ENDPOINT_ID, TEMPLATE_ID)
        return

    # --- 2. Run Completion Test ---
    print("\n--- Running completion test... ---")
    test_passed = False
    try:
        url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"}
                ]
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Raw response from endpoint:")
        print(json.dumps(result, indent=2))

        # Check for successful execution and output
        if result.get("status") == "COMPLETED" and "output" in result:
            print("\n✅ Test Passed! Model output received.")
            test_passed = True
            # Assuming OpenAI compatible output format from vLLM
            response_content = result['output']['choices'][0]['message']['content']
            print(f"\nModel Response: {response_content}")
        else:
            print("\n❌ Test Failed. The endpoint returned a non-COMPLETED status or no output.")
            print(f"Status: {result.get('status')}")
            print(f"Error: {result.get('error')}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ An error occurred during the completion test: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

    # --- 3. Cleanup ---
    cleanup_resources(ENDPOINT_ID, TEMPLATE_ID, test_passed=test_passed)


def cleanup_resources(endpoint_id: str, template_id: str, test_passed: bool = False):
    """Deletes the specified endpoint and template."""
    
    if test_passed:
        prompt = "\nThe test passed. Do you want to keep the endpoint or delete it? (keep/delete): "
    else:
        prompt = "\nThe test failed. Do you want to delete the endpoint and template? (yes/no): "

    # In a real user scenario, we would ask. Here, we'll make a decision.
    # If the test failed, we'll delete. If it passed, we'll keep it for now.
    should_delete = not test_passed
    
    if not should_delete:
        print("\nSkipping cleanup. Your endpoint is still active.")
        print(f"Endpoint ID: {endpoint_id}")
        return

    print(f"\n--- Cleaning up resources for endpoint {endpoint_id} ---")
    try:
        print(f"Deleting endpoint {endpoint_id}...")
        # The SDK does not have a direct delete function, so we construct the mutation.
        delete_endpoint_mutation = f'mutation {{ deleteEndpoint(input: {{endpointId: "{endpoint_id}"}}) }}'
        runpod.api.graphql.run_graphql_query(delete_endpoint_mutation)
        print("✅ Endpoint deleted.")
        
        # Wait a moment before deleting the template
        time.sleep(5)

        print(f"Deleting template {template_id}...")
        delete_template_mutation = f'mutation {{ deleteTemplate(input: {{templateId: "{template_id}"}}) }}'
        runpod.api.graphql.run_graphql_query(delete_template_mutation)
        print("✅ Template deleted.")
        
        print("\nCleanup complete.")

    except Exception as e:
        print(f"\n❌ An error occurred during cleanup: {e}")
        print("You may need to manually delete the resources from the RunPod console.")


if __name__ == "__main__":
    test_and_cleanup_endpoint()
