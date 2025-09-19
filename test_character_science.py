#!/usr/bin/env python3
"""
Test script for character science evaluation system.
This script tests the configuration generation without running full evaluations.
"""

import json
import tempfile
from pathlib import Path
from character_science import (
    load_character_definitions,
    create_modified_character_config,
    save_modified_character_config,
    CHARACTER_CONFIGS
)

def test_character_config_generation():
    """Test that character configurations are generated correctly."""
    print("🧪 Testing Character Science Configuration Generation")
    print("=" * 60)
    
    # Load character definitions
    char_definitions = load_character_definitions()
    if not char_definitions:
        print("❌ Failed to load character definitions")
        return False
    
    print(f"✅ Loaded {len(char_definitions)} character definitions")
    
    # Test Gemini ablations
    print("\n🔬 Testing Gemini Ablations...")
    gemini_configs = CHARACTER_CONFIGS["gemini_ablations"]["configurations"]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for config in gemini_configs:
            print(f"\n📋 Testing: {config['name']}")
            print(f"   Description: {config['description']}")
            print(f"   Base Character: {config['base_character']}")
            print(f"   Removed Traits: {config['removed_traits']}")
            
            try:
                # Create modified configuration
                modified_config = create_modified_character_config(
                    config["base_character"],
                    config["removed_traits"],
                    char_definitions
                )
                
                # Save configuration
                config_path = save_modified_character_config(
                    config["id"], 
                    modified_config, 
                    temp_path
                )
                
                # Verify the file was created
                if config_path.exists():
                    print(f"   ✅ Configuration saved to: {config_path}")
                    
                    # Load and verify the configuration
                    with open(config_path, 'r') as f:
                        saved_config = json.load(f)
                    
                    if config["id"] in saved_config:
                        char_config = saved_config[config["id"]]
                        print(f"   ✅ Configuration loaded successfully")
                        print(f"   📊 Traits: {len(char_config.get('traits', []))}")
                        print(f"   📊 Evaluations: {len(char_config.get('evaluations', []))}")
                        
                        # Show first few traits
                        traits = char_config.get('traits', [])
                        if traits:
                            print(f"   🔍 Sample traits:")
                            for i, trait in enumerate(traits[:3]):
                                print(f"      {i+1}. {trait[:80]}...")
                            if len(traits) > 3:
                                print(f"      ... and {len(traits) - 3} more")
                    else:
                        print(f"   ❌ Configuration not found in saved file")
                        return False
                else:
                    print(f"   ❌ Configuration file not created")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Error creating configuration: {e}")
                return False
    
    print(f"\n✅ All Gemini ablation configurations generated successfully!")
    
    # Test Clyde ablations
    print("\n🔬 Testing Clyde Ablations...")
    clyde_configs = CHARACTER_CONFIGS["clyde_ablations"]["configurations"]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for config in clyde_configs:
            print(f"\n📋 Testing: {config['name']}")
            
            try:
                # Create modified configuration
                modified_config = create_modified_character_config(
                    config["base_character"],
                    config["removed_traits"],
                    char_definitions
                )
                
                # Save configuration
                config_path = save_modified_character_config(
                    config["id"], 
                    modified_config, 
                    temp_path
                )
                
                if config_path.exists():
                    print(f"   ✅ Configuration saved successfully")
                else:
                    print(f"   ❌ Configuration file not created")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Error creating configuration: {e}")
                return False
    
    print(f"\n✅ All Clyde ablation configurations generated successfully!")
    
    return True

def test_trait_removal_logic():
    """Test that trait removal logic works correctly."""
    print("\n🔬 Testing Trait Removal Logic...")
    print("=" * 60)
    
    char_definitions = load_character_definitions()
    if not char_definitions:
        return False
    
    # Test with Gemini - remove "helpful" trait
    base_char = "gemini_helpful_assistant_backstory"
    removed_traits = ["helpful"]
    
    print(f"📋 Testing trait removal for: {base_char}")
    print(f"🗑️  Removing traits: {removed_traits}")
    
    # Get original traits
    original_traits = char_definitions[base_char].get("traits", [])
    print(f"📊 Original traits: {len(original_traits)}")
    
    # Create modified configuration
    modified_config = create_modified_character_config(
        base_char, removed_traits, char_definitions
    )
    
    # Check modified traits
    modified_traits = modified_config.get("traits", [])
    print(f"📊 Modified traits: {len(modified_traits)}")
    
    # Verify traits were actually removed
    removed_count = len(original_traits) - len(modified_traits)
    print(f"🗑️  Traits removed: {removed_count}")
    
    if removed_count > 0:
        print("✅ Trait removal working correctly")
        
        # Show what was removed
        print("\n🔍 Removed traits:")
        for trait in original_traits:
            if trait not in modified_traits:
                print(f"   - {trait}")
        
        # Show remaining traits
        print("\n🔍 Remaining traits:")
        for trait in modified_traits:
            print(f"   + {trait}")
        
        return True
    else:
        print("❌ No traits were removed - check removal logic")
        return False

def main():
    """Run all tests."""
    print("🚀 Character Science System Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test 1: Configuration generation
    if not test_character_config_generation():
        success = False
    
    # Test 2: Trait removal logic
    if not test_trait_removal_logic():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Character science system is ready to use.")
        print("\nNext steps:")
        print("1. Run: python character_science.py --config-type gemini_ablations --skip-evaluation")
        print("2. Check the generated configurations in the output directory")
        print("3. Run full evaluation: python character_science.py --config-type gemini_ablations")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
