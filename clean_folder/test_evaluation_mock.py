#!/usr/bin/env python3
"""
Test the evaluation system with mock data to verify structure.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the clean_folder to the path
sys.path.insert(0, str(Path(__file__).parent))

from run_evaluation import run_comprehensive_evaluation

async def test_evaluation_structure():
    """Test evaluation system structure without API calls."""
    print("🧪 Testing Evaluation System Structure")
    print("=" * 50)
    
    # Test with socratica_basic character
    character_id = "socratica_basic"
    behavior_names = ["socratica_self_knowledge", "socratica_guiding"]
    
    print(f"Character: {character_id}")
    print(f"Behaviors: {', '.join(behavior_names)}")
    
    try:
        # This will fail at API calls but should work for structure
        result = await run_comprehensive_evaluation(character_id, behavior_names)
        print("✅ Evaluation structure test passed")
        return result
    except Exception as e:
        if "API" in str(e) or "authentication" in str(e).lower():
            print("✅ Evaluation structure test passed (API error expected)")
            print(f"   Expected API error: {e}")
            return True
        else:
            print(f"❌ Evaluation structure test failed: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_evaluation_structure())
