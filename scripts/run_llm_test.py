
import os
import argparse
import subprocess
import time
import requests
import asyncio
from evals.llm_api import call_llm_api, load_vllm_lora_adapter

def kill_processes_on_port(port):
    """Find and kill any processes listening on the given port."""
    print(f"Attempting to kill processes on port {port}...")
    command = f"lsof -ti:{port}"
    try:
        pids_to_kill = subprocess.check_output(command, shell=True, text=True).strip().split('\n')
        if pids_to_kill and pids_to_kill[0]:
            for pid in pids_to_kill:
                print(f"Killing process with PID {pid} on port {port}")
                kill_command = f"kill -9 {pid}"
                subprocess.run(kill_command, shell=True, check=True)
            print(f"Successfully killed processes on port {port}.")
        else:
            print(f"No processes found on port {port}.")
    except subprocess.CalledProcessError:
        print(f"No processes found on port {port}.")
    except Exception as e:
        print(f"An error occurred while trying to kill processes on port {port}: {e}")

def setup_ssh_tunnel(local_port, remote_port, remote_host="runpod_a100_box"):
    """Establish an SSH tunnel in the background."""
    print(f"Setting up SSH tunnel: localhost:{local_port} -> {remote_host}:{remote_port}")
    # -f: go to background
    # -N: do not execute a remote command
    # -L: local port forwarding
    command = f"ssh -f -N -L {local_port}:localhost:{remote_port} {remote_host}"
    try:
        subprocess.run(command, shell=True, check=True)
        print("SSH tunnel command executed. Waiting a moment for it to establish...")
        time.sleep(2)  # Give the tunnel a moment to establish
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to set up SSH tunnel: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during tunnel setup: {e}")
        return False

def test_vllm_connection(port):
    """Test if the vLLM server is reachable on the given local port."""
    print(f"Testing connection to vLLM on localhost:{port}...")
    try:
        response = requests.get(f"http://localhost:{port}/health")
        if response.status_code == 200:
            print(f"✅ Connection successful! vLLM server is healthy.")
            return True
        else:
            print(f"❌ Connection failed. Status code: {response.status_code}, Response: {response.text}")
            return False
    except requests.ConnectionError as e:
        print(f"❌ Connection failed. Could not connect to localhost:{port}. Is the tunnel running?")
        print(f"   Error details: {e}")
        return False

async def main():
    parser = argparse.ArgumentParser(description="Run a test of the LLM API.")
    parser.add_argument('--use-runpod', type=bool, default=False, help='Set os.environ["VLLM_BACKEND_USE_RUNPOD"]')
    parser.add_argument('--model', type=str, default='rpotham/ft-0aa779f1-3d03-2025-08-05-01-10-16', help='The model to use.')
    parser.add_argument('--message', type=str, default='What is the capital of France?', help='The message to send to the LLM.')
    args = parser.parse_args()

    os.environ["VLLM_BACKEND_USE_RUNPOD"] = str(args.use_runpod)

    LOCAL_PORT = 7337
    REMOTE_PORT = 8000 # Default vLLM port

    if not args.use_runpod:
        kill_processes_on_port(LOCAL_PORT)
        if not setup_ssh_tunnel(LOCAL_PORT, REMOTE_PORT):
            raise Exception("Could not establish SSH tunnel.")
        if not test_vllm_connection(LOCAL_PORT):
            raise Exception("Could not connect to vLLM server.")

    try:
        print(f"Loading LoRA adapter: {args.model}...")
        load_vllm_lora_adapter(args.model)
        print("✅ LoRA adapter loaded successfully.")

        print("\nCalling model...")
        response = await call_llm_api(
            messages=[{"role": "user", "content": args.message}],
            model=args.model,
            caching=False,
        )
        if response.error:
            raise Exception(f"API call failed: {response.error}")
        
        print("\n✅ success")
        print(f"Response (truncated): {response.response_text[:200]}...")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

