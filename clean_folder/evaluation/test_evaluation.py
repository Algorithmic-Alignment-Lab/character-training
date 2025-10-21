#!/usr/bin/env python3
"""
Test script for the evaluation system.
"""


# Add evaluation directory to path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_imports():
    """Test that all imports work correctly."""
    try:
        from utils import load_config, load_character_definitions
        from bloom_eval import run_pipeline
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_character_definitions():
    """Test that character definitions can be loaded."""
    try:
        from utils import load_character_definitions
        characters = load_character_definitions()
        print(f"✅ Loaded {len(characters)} characters")
        for char_id, char_data in characters.items():
            print(f"  - {char_id}: {char_data.get('name', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Character definitions error: {e}")
        return False

def test_config_loading():
    """Test that config files can be loaded."""
    try:
        from utils import load_config
        config_path = "configs/bloom_settings_alex_helpfulness_claude-sonnet-4.yaml"
        config = load_config(config_path)
        print(f"✅ Config loaded: {config.get('behaviour', {}).get('name', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ Config loading error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing evaluation system...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_character_definitions,
        test_config_loading,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
