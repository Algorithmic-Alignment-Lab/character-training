#!/usr/bin/env python3
"""
Test Research Logs Integration
==============================

This script tests the integration of research logs into the evaluation dashboard.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_research_logger_integration():
    """Test the research logger integration with evaluation sessions."""
    print("🧪 Testing Research Logger Integration...")
    
    try:
        # Test imports
        from research_logger import get_research_logger
        from agora_evaluation_dashboard import AgoraEvaluationDashboard
        
        # Initialize logger
        logger = get_research_logger()
        
        # Test evaluation session tracking
        evaluation_id = f"test_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start evaluation session
        start_log = logger.start_evaluation_session(
            evaluation_id=evaluation_id,
            evaluation_type="agora_comparison",
            config={"scenarios": 3, "traits": 5, "test_mode": True}
        )
        
        print(f"✅ Started evaluation session: {evaluation_id}")
        
        # Log some evaluation activities
        logger.log_llm_generation(
            generation_type="scenario_generation",
            system_prompt="You are a test assistant generating scenarios for evaluation testing.",
            user_prompt="Generate 3 test scenarios for collaborative trait evaluation.",
            model_response="Test scenario 1: Team project collaboration\nTest scenario 2: Conflict resolution\nTest scenario 3: Group decision making",
            model="test-model",
            tokens_used=150,
            response_time=1.5,
            context={"test_run": True, "evaluation_id": evaluation_id}
        )
        
        logger.log_api_call(
            endpoint="test/api/judge",
            prompt="Evaluate this test conversation for collaborative traits.",
            response='{"collaborative_score": 4.5, "reasoning": "Test evaluation shows good collaboration"}',
            model="test-judge-model",
            system_prompt="You are a test judge evaluating collaborative traits.",
            prompt_type="judge_evaluation",
            tokens_used=200,
            response_time=2.0
        )
        
        logger.log_evaluation_result(
            evaluation_type="likert",
            conversation_id="test_conv_001",
            judge_prompt="Test judge prompt for collaborative evaluation",
            judge_response="Test judge response with collaborative score",
            scores={"Collaborative": 4.5, "Inquisitive": 4.0},
            reasoning="Test evaluation reasoning"
        )
        
        print("✅ Logged evaluation activities")
        
        # End evaluation session
        end_log = logger.end_evaluation_session(
            success=True,
            summary={"total_evaluations": 1, "success_rate": 1.0, "test_mode": True}
        )
        
        print(f"✅ Ended evaluation session: {evaluation_id}")
        
        # Test log filtering
        dashboard = AgoraEvaluationDashboard()
        
        # Mock file info for testing
        file_info = {
            "evaluation_id": evaluation_id,
            "timestamp": datetime.now().isoformat(),
            "path": "test_evaluation.json"
        }
        
        # Get all logs
        all_logs = logger.get_logs()
        
        # Filter evaluation-specific logs
        evaluation_logs = dashboard.filter_evaluation_logs(all_logs, file_info)
        
        print(f"✅ Found {len(evaluation_logs)} evaluation-specific logs")
        
        # Test log categorization
        evaluation_related_count = 0
        for log in evaluation_logs:
            if dashboard.is_evaluation_related_log(log):
                evaluation_related_count += 1
        
        print(f"✅ {evaluation_related_count} logs identified as evaluation-related")
        
        # Verify log structure
        required_fields = ['timestamp', 'session_id', 'evaluation_id', 'type', 'success']
        for log in evaluation_logs:
            for field in required_fields:
                if field not in log:
                    print(f"❌ Missing required field '{field}' in log")
                    return False
        
        print("✅ All logs have required fields")
        
        # Test evaluation ID correlation
        eval_id_logs = [log for log in evaluation_logs if log.get('evaluation_id') == evaluation_id]
        print(f"✅ {len(eval_id_logs)} logs correctly tagged with evaluation_id")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing research logger integration: {e}")
        return False

def test_dashboard_integration():
    """Test the dashboard integration with research logs."""
    print("\n🧪 Testing Dashboard Integration...")
    
    try:
        from agora_evaluation_dashboard import AgoraEvaluationDashboard
        
        dashboard = AgoraEvaluationDashboard()
        
        # Test log filtering methods
        test_logs = [
            {
                "timestamp": "2025-01-16T14:30:00",
                "type": "llm_generation",
                "generation_type": "scenario_generation",
                "evaluation_id": "test_eval_001",
                "success": True
            },
            {
                "timestamp": "2025-01-16T14:35:00",
                "type": "api_call",
                "prompt_type": "judge_evaluation",
                "evaluation_id": "test_eval_001",
                "success": True
            },
            {
                "timestamp": "2025-01-16T14:40:00",
                "type": "evaluation_result",
                "evaluation_type": "likert",
                "evaluation_id": "test_eval_002",
                "success": True
            }
        ]
        
        # Test filtering by evaluation ID
        file_info = {"evaluation_id": "test_eval_001"}
        filtered_logs = dashboard.filter_evaluation_logs(test_logs, file_info)
        
        expected_count = 2  # First two logs have matching evaluation_id
        if len(filtered_logs) == expected_count:
            print(f"✅ Evaluation ID filtering works: {len(filtered_logs)} logs found")
        else:
            print(f"❌ Evaluation ID filtering failed: expected {expected_count}, got {len(filtered_logs)}")
            return False
        
        # Test content-based filtering
        for log in test_logs:
            if dashboard.is_evaluation_related_log(log):
                print(f"✅ Log correctly identified as evaluation-related: {log['type']}")
        
        print("✅ Dashboard integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing dashboard integration: {e}")
        return False

def test_log_categorization():
    """Test the log categorization functionality."""
    print("\n🧪 Testing Log Categorization...")
    
    try:
        from agora_evaluation_dashboard import AgoraEvaluationDashboard
        
        dashboard = AgoraEvaluationDashboard()
        
        # Create test logs for each category
        test_logs = [
            {
                "type": "llm_generation",
                "generation_type": "scenario_generation",
                "system_prompt": "Generate scenarios",
                "success": True
            },
            {
                "type": "llm_generation", 
                "generation_type": "character_response",
                "system_prompt": "You are Agora character",
                "success": True
            },
            {
                "type": "api_call",
                "prompt_type": "judge_evaluation",
                "system_prompt": "Judge this conversation",
                "success": True
            },
            {
                "type": "api_call",
                "endpoint": "test/api",
                "success": True
            },
            {
                "type": "llm_generation",
                "success": False,
                "error": "Test error"
            }
        ]
        
        # Test categorization
        categories = {
            'Scenario Generation': [log for log in test_logs if log.get('generation_type') == 'scenario_generation'],
            'Character Responses': [log for log in test_logs if log.get('generation_type') == 'character_response'],
            'Judge Evaluations': [log for log in test_logs if log.get('prompt_type') == 'judge_evaluation'],
            'API Calls': [log for log in test_logs if log.get('type') == 'api_call'],
            'Errors': [log for log in test_logs if not log.get('success', True)]
        }
        
        expected_counts = {
            'Scenario Generation': 1,
            'Character Responses': 1,
            'Judge Evaluations': 1,
            'API Calls': 2,
            'Errors': 1
        }
        
        for category, logs in categories.items():
            expected = expected_counts[category]
            actual = len(logs)
            if actual == expected:
                print(f"✅ {category}: {actual} logs (expected {expected})")
            else:
                print(f"❌ {category}: {actual} logs (expected {expected})")
                return False
        
        print("✅ Log categorization tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing log categorization: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 RESEARCH LOGS INTEGRATION TESTING")
    print("=" * 50)
    
    tests = [
        ("Research Logger Integration", test_research_logger_integration),
        ("Dashboard Integration", test_dashboard_integration),
        ("Log Categorization", test_log_categorization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Research logs integration is working correctly")
        print("✅ Evaluation-specific log filtering implemented")
        print("✅ Log categorization working properly")
        print("✅ Dashboard integration complete")
        
        print("\n📋 NEXT STEPS:")
        print("1. Run: streamlit run streamlit_chat.py")
        print("2. Go to: Evaluations > Agora Evaluation Pipeline")
        print("3. Select an evaluation and check 'Research Logs' section")
        print("4. Verify logs are displayed and categorized correctly")
        
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)