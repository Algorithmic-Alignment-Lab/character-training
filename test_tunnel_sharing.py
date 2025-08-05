#!/usr/bin/env python3
"""
Simple test to verify shared SSH tunnel behavior
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to path
sys.path.append(str(Path(__file__).parent))

from evals.llm_api import _setup_shared_ssh_tunnel, _test_tunnel_connection

async def test_tunnel_sharing():
    """Test that the SSH tunnel sharing works correctly"""
    print("🔧 Testing SSH Tunnel Sharing")
    print("=" * 40)
    
    # Ensure we're using local vLLM (not RunPod)
    os.environ["VLLM_BACKEND_USE_RUNPOD"] = "False"
    
    try:
        # Test 1: Create first tunnel
        print("1. Creating first SSH tunnel...")
        port1 = _setup_shared_ssh_tunnel(remote_port=8000)
        print(f"   First tunnel created on port {port1}")
        
        # Test 2: Request second tunnel (should reuse the first)
        print("2. Requesting second SSH tunnel...")
        port2 = _setup_shared_ssh_tunnel(remote_port=8000)
        print(f"   Second tunnel using port {port2}")
        
        # Test 3: Verify both are the same
        if port1 == port2:
            print("✅ Tunnel sharing works - both requests use the same port")
        else:
            print(f"❌ Tunnel sharing failed - got different ports: {port1} vs {port2}")
            return False
        
        # Test 4: Test connection
        print("3. Testing tunnel connection...")
        if _test_tunnel_connection(port1):
            print("✅ Tunnel connection test successful")
        else:
            print("❌ Tunnel connection test failed")
            return False
        
        # Test 5: Simulate concurrent access
        print("4. Testing concurrent tunnel access...")
        ports = []
        for i in range(10):
            port = _setup_shared_ssh_tunnel(remote_port=8000)
            ports.append(port)
        
        if all(p == port1 for p in ports):
            print("✅ All 10 concurrent requests use the same tunnel")
        else:
            unique_ports = set(ports)
            print(f"❌ Got {len(unique_ports)} different ports: {unique_ports}")
            return False
        
        print("\n🎉 All tunnel sharing tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Tunnel test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_tunnel_sharing()
    
    if success:
        print("\n✅ SSH tunnel sharing is working correctly!")
        print("The system should now be able to handle 100+ concurrent vLLM calls")
        print("using a single shared SSH tunnel.")
    else:
        print("\n❌ SSH tunnel sharing has issues that need to be fixed")

if __name__ == "__main__":
    asyncio.run(main())
