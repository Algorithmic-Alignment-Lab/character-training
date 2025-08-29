import os
import asyncio
import json
from run_scalable_llm_runpod import RunPodConfig, RunPodScalableInference, ScalingMode

async def test_runpod_inference():
    """
    Tests the RunPod autoscaling inference using the RunPodScalableInference class.
    1. Sets up configuration from environment variables.
    2. Performs a health check on the endpoint.
    3. Runs a test inference call.
    """
    print("--- Testing RunPod Autoscaling Inference with RunPodScalableInference ---")

    # 1. Set up configuration from environment variables
    endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID")
    api_key = os.environ.get("RUNPOD_API_KEY")

    if not endpoint_id or not api_key:
        print("❌ RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY environment variables must be set.")
        print("Please set RUNPOD_ENDPOINT_ID to your RunPod serverless endpoint ID.")
        return

    print(f"✅ Using RUNPOD_ENDPOINT_ID: {endpoint_id}")
    print("✅ RUNPOD_API_KEY is set.")

    config = RunPodConfig(
        endpoint_id=endpoint_id,
        api_key=api_key,
        model_name="rpotham/ft-0aa779f1-3d03-2025-08-05-01-10-16", # The model/adapter to use
        scaling_mode=ScalingMode.SERVERLESS,
    )

    async with RunPodScalableInference(config) as inference:
        try:
            # 2. Perform a health check
            print("\nPerforming health check...")
            is_healthy = await inference.health_check()
            if not is_healthy:
                print("❌ Endpoint is not healthy or not running. Please check your RunPod dashboard.")
                status = await inference.get_endpoint_status()
                print(f"Current endpoint status: {json.dumps(status, indent=2)}")
                return
            
            print("✅ Endpoint is healthy and running.")

            # 3. Run a test inference call
            print("\nCalling model via RunPod...")
            messages = [{"role": "user", "content": "What is the capital of France?"}]
            
            result = await inference.run_inference(
                messages=messages,
                temperature=0.2,
                max_tokens=128
            )

            if result.get("success"):
                print("\n✅ API call successful.")
                print("Response Data:", json.dumps(result.get('data'), indent=2))
                # The actual model output is usually nested inside the 'data' and 'output' keys
                model_output = result.get('data', {}).get('output', {})
                if model_output:
                    # Assuming OpenAI compatible output format
                    response_content = model_output.get('choices', [{}])[0].get('message', {}).get('content', 'No content found')
                    print("\nModel Response:", response_content)
                else:
                    print("\nCould not extract model output from the response.")

            else:
                print(f"\n❌ An error occurred during API call: {result.get('error')}")

            # Print metrics
            print("\n--- Metrics ---")
            print(json.dumps(inference.get_metrics(), indent=2))

        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()
            print("\nPlease check your RunPod endpoint configuration and ensure it's active.")

if __name__ == "__main__":
    # To run an async function from a script
    # You might need to set the endpoint ID, e.g.
    # export RUNPOD_ENDPOINT_ID='pmave9bk168p0q'
    asyncio.run(test_runpod_inference())
