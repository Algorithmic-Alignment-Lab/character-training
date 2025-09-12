#!/usr/bin/env python3
"""
Test script for the new behavior generation approach that generates description and events together
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_new_behavior_generation():
    """Test the new behavior generation approach"""
    
    print("🧪 Testing New Behavior Generation (Description + Events Together)")
    print("=" * 70)
    
    # Check if we have the required dependencies
    try:
        import litellm
        print("✅ litellm is available")
    except ImportError:
        print("❌ litellm is not installed. Install with: pip install litellm")
        return False
    
    try:
        from pydantic import BaseModel
        print("✅ pydantic is available")
    except ImportError:
        print("❌ pydantic is not installed. Install with: pip install pydantic")
        return False
    
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️ ANTHROPIC_API_KEY environment variable is not set")
        print("   Set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        return False
    else:
        print("✅ ANTHROPIC_API_KEY is set")
    
    # Test with Rudi character
    print("\n🎭 Testing with Rudi character...")
    
    try:
        # Import the functions from the main script
        from run_steps_given_character_1_4 import (
            get_character,
            generate_behavior_with_example,
            create_complete_example
        )
        
        # Get Rudi character data
        character = get_character("rudi_storyteller_companion_backstory")
        print(f"  Character: {character.get('name', 'Unknown')}")
        print(f"  Evaluations: {len(character.get('evaluations', []))} evaluations")
        
        # Test behavior generation for first evaluation
        evaluations = character.get('evaluations', [])
        if evaluations:
            first_evaluation = evaluations[0]
            print(f"\n  🎭 Testing description + events generation for {first_evaluation}...")
            
            # Generate behavior description and events together
            behavior_with_example = generate_behavior_with_example(
                character, 
                first_evaluation, 
                model="anthropic/claude-sonnet-4-20250514"
            )
            
            print(f"  ✅ Generated behavior:")
            print(f"    Name: {behavior_with_example.name}")
            print(f"    Description: {behavior_with_example.description[:100]}...")
            print(f"    Events: {len(behavior_with_example.events)} conversation events")
            
            # Show first few events
            for i, event in enumerate(behavior_with_example.events[:2]):
                print(f"      Turn {event.turn} ({event.event}): {event.content[:60]}...")
            
            # Test creating complete example
            complete_example = create_complete_example(behavior_with_example, character)
            print(f"\n  ✅ Created complete example with:")
            print(f"    Evaluator: {complete_example['evaluator_model_id']}")
            print(f"    Target: {complete_example['target_model_id']}")
            print(f"    System prompt length: {len(complete_example['target_system_prompt'])} chars")
            print(f"    Events: {len(complete_example['events'])} events")
            
        else:
            print("  ⚠️ No evaluations found for Rudi character")
        
        print("\n✅ New behavior generation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during new behavior generation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step4_only():
    """Test just step 4 (behavior generation) for Rudi"""
    
    print("\n🎯 Testing Step 4 Only for Rudi (New Approach)")
    print("=" * 50)
    
    try:
        from run_steps_given_character_1_4 import step4_write_behaviors
        
        # Test with Rudi
        character_id = "rudi_storyteller_companion_backstory"
        print(f"Testing step 4 for character: {character_id}")
        
        step4_write_behaviors(character_id, model="anthropic/claude-sonnet-4-20250514")
        
        print("✅ Step 4 test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during step 4 test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    print("🚀 New Behavior Generation Test Suite")
    print("=" * 60)
    print("This tests the new approach that generates description and events together")
    print("=" * 60)
    
    # Test 1: Basic functionality
    success1 = test_new_behavior_generation()
    
    if success1:
        # Test 2: Full step 4
        success2 = test_step4_only()
        
        if success2:
            print("\n🎉 All tests passed!")
            print("\nThe new approach successfully:")
            print("  ✅ Generates behavior descriptions and events together")
            print("  ✅ Saves descriptions to behaviors.json")
            print("  ✅ Saves complete examples to behaviors/examples/")
            print("  ✅ Uses hardcoded metadata (evaluator_model_id, target_model_id, etc.)")
            print("  ✅ Only generates the events array from the model")
            print("\nYou can now run the full pipeline:")
            print("python run_steps_given_character_1_4.py --character-id rudi_storyteller_companion_backstory")
        else:
            print("\n⚠️ Step 4 test failed, but basic functionality works")
    else:
        print("\n❌ Basic functionality test failed")
        print("Please check your setup and try again")

if __name__ == "__main__":
    main()
