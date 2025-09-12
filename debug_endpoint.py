#!/usr/bin/env python3
"""
Debug script to inspect endpoint details and logs
"""

import runpod
from dotenv import load_dotenv
import time
import os

def debug_endpoint():
    """Debug the endpoint status and get detailed information"""
    
    # Load environment variables
    load_dotenv()
    
    # Set the API key for runpod
    runpod.api_key = os.getenv("RUNPOD_API_KEY")
    
    ENDPOINT_ID = "vllm-pw2h94fjhm9rvf"
    
    print(f"🔍 Debugging endpoint: {ENDPOINT_ID}")
    print(f"API Key set: {'Yes' if runpod.api_key else 'No'}")
    
    # Get endpoint details
    try:
        endpoints = runpod.get_endpoints()
        endpoint = next((ep for ep in endpoints if ep['id'] == ENDPOINT_ID), None)
        
        if not endpoint:
            print(f"❌ Endpoint {ENDPOINT_ID} not found")
            return
        
        print(f"\n📊 Endpoint Details:")
        print(f"  Name: {endpoint.get('name', 'N/A')}")
        print(f"  ID: {endpoint.get('id', 'N/A')}")
        print(f"  Status: {endpoint.get('status', 'N/A')}")
        print(f"  Workers Running: {endpoint.get('workersRunning', 0)}")
        print(f"  Workers Idle: {endpoint.get('workersIdle', 0)}")
        print(f"  Template ID: {endpoint.get('template', {}).get('id', 'N/A')}")
        
        # Get worker details if available
        if 'workers' in endpoint and endpoint['workers']:
            print(f"\n👷 Workers:")
            for i, worker in enumerate(endpoint['workers']):
                print(f"  Worker {i+1}:")
                print(f"    ID: {worker.get('id', 'N/A')}")
                print(f"    Status: {worker.get('status', 'N/A')}")
                print(f"    Runtime: {worker.get('runtime', {}).get('uptimeInSeconds', 0)} seconds")
                if 'logs' in worker:
                    print(f"    Logs: {worker.get('logs', 'No logs')}")
        
        # Try to get recent jobs
        print(f"\n📋 Checking for recent jobs...")
        # Note: RunPod SDK might not have direct job history access
        
    except Exception as e:
        print(f"❌ Error getting endpoint details: {e}")

if __name__ == "__main__":
    debug_endpoint()
