import argparse
import logging
import os
import subprocess
import requests
import time
import threading

# Global state for SSH tunnel management
_ssh_tunnel_lock = threading.Lock()
_ssh_tunnel_pid = None
_ssh_tunnel_port = 7337

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_available_port(base_port=7337, max_attempts=50):
    """Find an available port starting from base_port"""
    for i in range(max_attempts):
        port = base_port + i
        try:
            # Check if port is in use
            result = subprocess.run(
                f"lsof -ti:{port}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            if not result.stdout.strip():  # Port is free
                return port
        except (subprocess.TimeoutExpired, Exception):
            continue
    raise Exception(f"Could not find available port after {max_attempts} attempts")

def _test_tunnel_connection(port, timeout=10):
    """Test if SSH tunnel is working by checking if port is accessible"""
    try:
        # In a real scenario, this would be a more specific health check endpoint.
        # For this test, we'll assume the presence of the root URL is enough.
        url = f"http://localhost:{port}/"
        # We don't expect a 200 on /, but a connection should be established
        requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        logger.warning(f"Connection error on port {port}. Tunnel may not be ready.")
        return False
    except Exception as e:
        logger.error(f"Error testing tunnel connection on port {port}: {e}")
        return False


def _setup_shared_ssh_tunnel(remote_port, host="runpod_a100_box", max_retries=3):
    """Setup a single shared SSH tunnel that can handle multiple concurrent connections"""
    global _ssh_tunnel_pid, _ssh_tunnel_port

    with _ssh_tunnel_lock:
        if _ssh_tunnel_pid is not None:
            try:
                os.kill(_ssh_tunnel_pid, 0)
                if _test_tunnel_connection(_ssh_tunnel_port):
                    logger.info(f"Reusing existing SSH tunnel on port {_ssh_tunnel_port} (PID: {_ssh_tunnel_pid})")
                    return _ssh_tunnel_port
                else:
                    logger.warning(f"SSH tunnel process exists but connection test failed")
            except OSError:
                logger.info(f"SSH tunnel process {_ssh_tunnel_pid} is dead, creating new tunnel")
                _ssh_tunnel_pid = None

        for attempt in range(max_retries):
            try:
                local_port = _get_available_port(_ssh_tunnel_port)
                subprocess.run(f"lsof -ti:{local_port} | xargs -r kill -9", shell=True)
                time.sleep(1)

                cmd = f"ssh -N -L {local_port}:localhost:{remote_port} {host}"
                logger.info(f"Starting SSH tunnel: {cmd}")
                process = subprocess.Popen(cmd, shell=True)

                time.sleep(3) # Give tunnel time to establish

                # A simple connection test might be needed here in a real case
                # For now, we'll assume it works if the process starts.
                # A better test would be `_test_tunnel_connection`
                if process.poll() is None: # check if process is running
                    _ssh_tunnel_pid = process.pid
                    _ssh_tunnel_port = local_port
                    logger.info(f"SSH tunnel established on port {local_port} (PID: {process.pid})")
                    return local_port
                else:
                    logger.warning(f"Tunnel process exited unexpectedly, attempt {attempt + 1}")

            except Exception as e:
                logger.warning(f"SSH tunnel setup failed, attempt {attempt + 1}: {e}")
                time.sleep(2)

        raise Exception(f"Failed to establish SSH tunnel after {max_retries} attempts")


def get_vllm_api_base(use_runpod: bool, runpod_endpoint_id: str = "pmave9bk168p0q"):
    """
    Determines the vLLM API base URL.

    If use_runpod is True, it returns the RunPod API endpoint.
    If use_runpod is False, it sets up an SSH tunnel and returns the local URL.
    """
    if use_runpod:
        vllm_api_base = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/openai"
        logger.info(f"Using RunPod endpoint: {vllm_api_base}")
        return vllm_api_base
    else:
        logger.info("Setting up local SSH tunnel for vLLM access.")
        try:
            # Assuming remote vLLM runs on port 8000
            remote_port = 8000
            local_port = _setup_shared_ssh_tunnel(remote_port)
            vllm_api_base = f"http://localhost:{local_port}/v1"
            logger.info(f"Using local vLLM endpoint via SSH tunnel: {vllm_api_base}")
            return vllm_api_base
        except Exception as e:
            logger.error(f"Failed to setup SSH tunnel: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Test RunPod scaling toggle.")
    parser.add_argument("--use-runpod", action="store_true", help="Use RunPod for vLLM backend.")
    args = parser.parse_args()

    os.environ["VLLM_BACKEND_USE_RUNPOD"] = "True" if args.use_runpod else "False"
    logger.info(f"VLLM_BACKEND_USE_RUNPOD set to: {os.environ['VLLM_BACKEND_USE_RUNPOD']}")

    try:
        api_base_url = get_vllm_api_base(use_runpod=args.use_runpod)
        print(f"Successfully determined vLLM API base URL: {api_base_url}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup the SSH tunnel if it was created
        global _ssh_tunnel_pid
        if _ssh_tunnel_pid is not None:
            logger.info(f"Cleaning up SSH tunnel (PID: {_ssh_tunnel_pid})...")
            try:
                os.kill(_ssh_tunnel_pid, 9)
            except OSError:
                pass # Process might already be gone


if __name__ == "__main__":
    main()

