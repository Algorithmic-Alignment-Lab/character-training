#!/usr/bin/env python3
"""
Test script to verify concurrent vLLM calls work properly with the improved SSH tunnel management
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to path
sys.path.append(str(Path(__file__).parent))

from evals.llm_api import call_llm_api

# Test configuration
model_id = "rpotham/ft-0aa779f1-3d03-2025-08-05-01-10-16"
messages = [{"role": "user", "content": "What is the capital of France? (Answer briefly)"}]

# Ensure we're using local vLLM (not RunPod)
os.environ["VLLM_BACKEND_USE_RUNPOD"] = "False"

async def single_vllm_call(call_id):
    """Make a single vLLM API call"""
    # Only log every 10th call to avoid spam
    if call_id % 10 == 1 or call_id <= 5:
        print(f"🚀 Starting call {call_id}")
    
    try:
        response = await call_llm_api(
            messages=messages,
            model=model_id,
            temperature=0.0,
            max_tokens=50,
            caching=False,
        )
        
        if response.error:
            if call_id % 10 == 1 or call_id <= 5:
                print(f"❌ Call {call_id} failed: {response.error}")
            return False
        else:
            if call_id % 10 == 1 or call_id <= 5:
                print(f"✅ Call {call_id} success: {response.response_text[:50]}...")
            return True
            
    except Exception as e:
        if call_id % 10 == 1 or call_id <= 5:
            print(f"❌ Call {call_id} exception: {e}")
        return False

async def test_concurrent_calls(num_calls=5):
    """Test multiple concurrent vLLM calls"""
    print(f"=== Testing {num_calls} Concurrent vLLM Calls ===")
    print("This tests if the shared SSH tunnel and LoRA loading can handle concurrent requests")
    print("All calls should share the same SSH tunnel and LoRA adapter")
    print()
    
    # Start all calls concurrently
    tasks = [single_vllm_call(i+1) for i in range(num_calls)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Analyze results
    successful_calls = sum(1 for result in results if result is True)
    failed_calls = len(results) - successful_calls
    
    print(f"\n=== Results ===")
    print(f"Successful calls: {successful_calls}/{num_calls}")
    print(f"Failed calls: {failed_calls}/{num_calls}")
    
    if successful_calls == num_calls:
        print("🎉 All concurrent calls succeeded!")
        return True
    elif successful_calls > 0:
        print("⚠️ Some calls succeeded, some failed - check tunnel sharing")
        return False
    else:
        print("💥 All calls failed - check SSH tunnel and vLLM server")
        return False

async def test_sequential_vs_concurrent():
    """Compare sequential vs concurrent call performance"""
    print("\n=== Testing Sequential vs Concurrent Performance ===")
    
    # Test sequential calls
    print("Testing 3 sequential calls...")
    start_time = asyncio.get_event_loop().time()
    for i in range(3):
        await single_vllm_call(f"seq-{i+1}")
    sequential_time = asyncio.get_event_loop().time() - start_time
    
    print(f"Sequential time: {sequential_time:.2f} seconds")
    
    # Test concurrent calls
    print("\nTesting 3 concurrent calls...")
    start_time = asyncio.get_event_loop().time()
    tasks = [single_vllm_call(f"conc-{i+1}") for i in range(3)]
    await asyncio.gather(*tasks, return_exceptions=True)
    concurrent_time = asyncio.get_event_loop().time() - start_time
    
    print(f"Concurrent time: {concurrent_time:.2f} seconds")
    
    if concurrent_time < sequential_time:
        print(f"🚀 Concurrent calls are {sequential_time/concurrent_time:.1f}x faster!")
    else:
        print("⚠️ Concurrent calls didn't improve performance - check implementation")

async def main():
    """Main test function"""
    print("🧪 Testing Concurrent vLLM API Calls with Shared SSH Tunnel")
    print("=" * 60)
    
    # Test 1: Small scale test
    print("Phase 1: Basic functionality test")
    success = await test_concurrent_calls(3)
    
    if success:
        # Test 2: Medium scale test  
        print("\nPhase 2: Medium scale test")
        success = await test_concurrent_calls(10)
        
        if success:
            # Test 3: Large scale test - 100 concurrent calls
            print("\nPhase 3: Large scale test - 100 concurrent calls")
            success = await test_concurrent_calls(100)
            
            if success:
                print("\n🎉 SUCCESS: System can handle 100 concurrent vLLM calls!")
                
                # Test 4: Performance comparison
                await test_sequential_vs_concurrent()
            else:
                print("\n❌ Large scale test failed - system may not handle 100 concurrent calls")
        else:
            print("\n❌ Medium scale test failed - fixing issues before large scale testing")
    else:
        print("\n❌ Basic functionality test failed - fixing issues before scaling up")
    
    print("\n=== Test Complete ===")
    print("The shared SSH tunnel approach should allow many concurrent connections")
    print("without port conflicts or resource exhaustion.")

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
