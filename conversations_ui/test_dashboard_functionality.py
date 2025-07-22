#!/usr/bin/env python3
"""
Test Dashboard Functionality
============================

This script tests the dashboard to ensure all tabs are working correctly
with the sample data.
"""

import os
import json
import sys
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_sample_data_exists():
    """Test that sample data files exist."""
    print("🔍 Testing sample data existence...")
    
    evaluation_dir = "evaluation_results"
    expected_files = [
        "evaluation_report_20250116_143000.json",
        "test_scenarios_20250116_143000.json"
    ]
    
    for file in expected_files:
        file_path = os.path.join(evaluation_dir, file)
        if os.path.exists(file_path):
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
            return False
    
    return True

def test_evaluation_data_structure():
    """Test that evaluation data has the correct structure."""
    print("\n🔍 Testing evaluation data structure...")
    
    file_path = "evaluation_results/evaluation_report_20250116_143000.json"
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Check required sections
        required_sections = ['evaluation_summary', 'likert_evaluation', 'elo_comparison']
        for section in required_sections:
            if section in data:
                print(f"✅ Found section: {section}")
            else:
                print(f"❌ Missing section: {section}")
                return False
        
        # Check evaluation summary
        summary = data['evaluation_summary']
        if 'scenarios_tested' in summary and 'traits_evaluated' in summary:
            print(f"✅ Evaluation summary complete: {summary['scenarios_tested']} scenarios, {len(summary['traits_evaluated'])} traits")
        else:
            print("❌ Evaluation summary incomplete")
            return False
        
        # Check likert evaluation
        likert = data['likert_evaluation']
        if 'agora_original' in likert and 'agora_with_backstory' in likert:
            print("✅ Likert evaluation data complete")
        else:
            print("❌ Likert evaluation data incomplete")
            return False
        
        # Check ELO comparison
        elo = data['elo_comparison']
        if 'trait_wins' in elo and 'total_comparisons' in elo:
            print("✅ ELO comparison data complete")
        else:
            print("❌ ELO comparison data incomplete")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading evaluation data: {e}")
        return False

def test_dashboard_imports():
    """Test that dashboard modules can be imported."""
    print("\n🔍 Testing dashboard imports...")
    
    try:
        from agora_evaluation_dashboard import AgoraEvaluationDashboard
        print("✅ Successfully imported AgoraEvaluationDashboard")
        
        # Test instantiation
        dashboard = AgoraEvaluationDashboard()
        print("✅ Successfully instantiated dashboard")
        
        # Test file finding
        files = dashboard.find_evaluation_files()
        if files:
            print(f"✅ Found {len(files)} evaluation files")
        else:
            print("❌ No evaluation files found")
            return False
        
        # Test data loading
        first_file = files[0]
        summary = dashboard.load_evaluation_summary(first_file['path'])
        if summary:
            print("✅ Successfully loaded evaluation summary")
        else:
            print("❌ Failed to load evaluation summary")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing dashboard: {e}")
        return False

def test_research_logging():
    """Test research logging functionality."""
    print("\n🔍 Testing research logging...")
    
    try:
        from research_logger import get_research_logger
        
        logger = get_research_logger()
        print("✅ Successfully created research logger")
        
        # Test logging functionality
        logger.log_prompt_test(
            prompt_type="test",
            prompt_version="v1",
            input_data={"test": "input"},
            output_data={"test": "output"}
        )
        print("✅ Successfully logged test data")
        
        # Test retrieving logs
        logs = logger.get_logs(last_n=1)
        if logs:
            print(f"✅ Successfully retrieved {len(logs)} log entries")
        else:
            print("❌ No logs found after logging")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing research logging: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 TESTING DASHBOARD FUNCTIONALITY")
    print("=" * 50)
    
    tests = [
        test_sample_data_exists,
        test_evaluation_data_structure,
        test_dashboard_imports,
        test_research_logging
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Dashboard should work correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)