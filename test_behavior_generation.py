#!/usr/bin/env python3
"""
Test script for the behavior generation functionality in run_steps_given_character_1_4.py
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_behavior_generation():
    """Test the behavior generation functionality"""
    
    print("🧪 Testing Behavior Generation")
    print("=" * 50)
    
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
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY environment variable is not set")
        print("   Set it with: export OPENAI_API_KEY='your-api-key-here'")
        return False
    else:
        print("✅ OPENAI_API_KEY is set")
    
    # Check if character definitions exist
    char_def_path = project_root / "auto_eval_gen" / "character_definitions.json"
    if not char_def_path.exists():
        print(f"❌ Character definitions file not found: {char_def_path}")
        return False
    else:
        print("✅ Character definitions file exists")
    
    # Test with a simple character
    print("\n🎭 Testing with Socratica character...")
    
    try:
        # Import the functions from the main script
        from run_steps_given_character_1_4 import (
            get_character,
            generate_behaviors_for_character,
            generate_behavior_example,
            BehaviorDefinition
        )
        
        # Get Socratica character data
        character = get_character("socratica_research_librarian_backstory")
        print(f"  Character: {character.get('name', 'Unknown')}")
        print(f"  Traits: {len(character.get('traits', []))} traits")
        
        # Test behavior generation
        print("  🤖 Generating behaviors...")
        behaviors = generate_behaviors_for_character(character, model="gpt-4o-2024-08-06")
        
        print(f"  ✅ Generated {len(behaviors.behaviors)} behaviors:")
        for behavior in behaviors.behaviors:
            print(f"    - {behavior.name}: {behavior.description[:100]}...")
        
        # Test example generation for first behavior
        if behaviors.behaviors:
            first_behavior = behaviors.behaviors[0]
            print(f"\n  🎭 Generating example for {first_behavior.name}...")
            example = generate_behavior_example(character, first_behavior, model="gpt-4o-2024-08-06")
            
            print(f"  ✅ Generated example with {len(example.events)} events:")
            for event in example.events[:2]:  # Show first 2 events
                print(f"    Turn {event.turn} ({event.event}): {event.content[:80]}...")
        
        print("\n✅ Behavior generation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during behavior generation test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step4_only():
    """Test just step 4 (behavior generation) for a character"""
    
    print("\n🎯 Testing Step 4 Only")
    print("=" * 30)
    
    try:
        from run_steps_given_character_1_4 import step4_write_behaviors
        
        # Test with Socratica
        character_id = "socratica_research_librarian_backstory"
        print(f"Testing step 4 for character: {character_id}")
        
        step4_write_behaviors(character_id, model="gpt-4o-2024-08-06")
        
        print("✅ Step 4 test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during step 4 test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    print("🚀 Behavior Generation Test Suite")
    print("=" * 60)
    
    # Test 1: Basic functionality
    success1 = test_behavior_generation()
    
    if success1:
        # Test 2: Full step 4
        success2 = test_step4_only()
        
        if success2:
            print("\n🎉 All tests passed!")
            print("\nYou can now run the full pipeline:")
            print("python run_steps_given_character_1_4.py --character-id socratica_research_librarian_backstory")
        else:
            print("\n⚠️ Step 4 test failed, but basic functionality works")
    else:
        print("\n❌ Basic functionality test failed")
        print("Please check your setup and try again")

if __name__ == "__main__":
    main()
