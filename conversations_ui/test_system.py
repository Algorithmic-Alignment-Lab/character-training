#!/usr/bin/env python3
"""
System Test for Agora Evaluation
================================

This script tests the system components and shows you what's working.
"""

import os
import sys
import traceback

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import plotly.express as px
        print("✅ Plotly imported")
    except ImportError as e:
        print(f"❌ Plotly import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ Pandas imported")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        from prompt_config import get_prompt_manager
        print("✅ Prompt config imported")
    except ImportError as e:
        print(f"❌ Prompt config import failed: {e}")
        return False
    
    try:
        from llm_api import call_llm_api
        print("✅ LLM API imported")
    except ImportError as e:
        print(f"❌ LLM API import failed: {e}")
        return False
    
    return True

def test_prompt_system():
    """Test the prompt management system."""
    print("\n🧪 Testing prompt system...")
    
    try:
        from prompt_config import get_prompt_manager
        pm = get_prompt_manager()
        
        # Test character cards
        agora_original = pm.get_character_card("agora_original")
        print(f"✅ Agora original prompt loaded ({len(agora_original)} chars)")
        
        agora_backstory = pm.get_character_card("agora_with_backstory")
        print(f"✅ Agora backstory prompt loaded ({len(agora_backstory)} chars)")
        
        # Test scenario generation
        scenario_prompt = pm.get_scenario_prompt(3)
        print(f"✅ Scenario prompt generated ({len(scenario_prompt)} chars)")
        
        # Test evaluation prompts
        test_conversation = {
            'system_prompt': agora_original[:100],
            'user_message': "Test user message",
            'assistant_response': "Test assistant response"
        }
        
        likert_prompt = pm.get_likert_prompt(test_conversation)
        print(f"✅ Likert prompt generated ({len(likert_prompt)} chars)")
        
        elo_prompt = pm.get_elo_prompt("Test formatted conversations", "Collaborative")
        print(f"✅ ELO prompt generated ({len(elo_prompt)} chars)")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt system test failed: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Test database functionality."""
    print("\n🗄️ Testing database...")
    
    try:
        from database import init_db, get_db_connection
        
        # Initialize test database
        test_db = "test_evaluation.db"
        init_db(test_db)
        print("✅ Database initialized")
        
        # Test connection
        with get_db_connection(test_db) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Database tables: {', '.join(tables)}")
        
        # Clean up
        if os.path.exists(test_db):
            os.remove(test_db)
            print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False

def show_next_steps():
    """Show the user what to do next."""
    print("\n🚀 NEXT STEPS:")
    print("=" * 50)
    
    print("\n1. Start the Streamlit dashboard:")
    print("   streamlit run streamlit_chat.py")
    
    print("\n2. Navigate to tabs:")
    print("   📝 'Prompt Testing' - Test and modify prompts")
    print("   📊 'Evaluations' - Run Agora evaluation pipeline")
    
    print("\n3. Or run evaluations directly:")
    print("   python demo_agora_pipeline.py  # Quick demo (3 scenarios)")
    print("   python run_agora_evaluation_pipeline.py --scenarios 5  # Small test")
    
    print("\n4. Files to check:")
    print("   📄 PROMPT_MANAGEMENT_GUIDE.md - Detailed prompt guide")
    print("   📄 QUICK_START_GUIDE.md - Step-by-step instructions")
    
    print("\n5. For debugging:")
    print("   python run_demo.py  # Interactive demo")
    print("   python launch_agora_evaluation.py all  # Complete suite")

def main():
    """Main test function."""
    print("🎯 AGORA EVALUATION SYSTEM TEST")
    print("=" * 60)
    
    # Change to correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_prompt_system():
        tests_passed += 1
    
    if test_database():
        tests_passed += 1
    
    # Show results
    print(f"\n📊 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! System is ready.")
        show_next_steps()
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n💡 Try installing missing dependencies:")
        print("   pip install streamlit plotly pandas")

if __name__ == "__main__":
    main()