#!/usr/bin/env python3
"""
Test Dashboard Components
========================

This script tests specific dashboard components to ensure they work correctly.
"""

import os
import json
import sys

def test_detailed_analysis_data():
    """Test that detailed analysis will display correctly."""
    print("🔍 Testing Detailed Analysis component...")
    
    try:
        from agora_evaluation_dashboard import AgoraEvaluationDashboard
        
        # Create dashboard instance
        dashboard = AgoraEvaluationDashboard()
        
        # Find evaluation files
        files = dashboard.find_evaluation_files()
        if not files:
            print("❌ No evaluation files found")
            return False
        
        # Load evaluation summary
        first_file = files[0]
        summary = dashboard.load_evaluation_summary(first_file['path'])
        if not summary:
            print("❌ Could not load evaluation summary")
            return False
        
        # Test radar chart data preparation
        if 'likert_evaluation' in summary:
            likert_data = summary['likert_evaluation']
            
            # Check for required versions
            if 'agora_original' in likert_data and 'agora_with_backstory' in likert_data:
                print("✅ Both Agora versions found in data")
                
                # Check trait averages
                original_traits = likert_data['agora_original'].get('trait_averages', {})
                backstory_traits = likert_data['agora_with_backstory'].get('trait_averages', {})
                
                if original_traits and backstory_traits:
                    print(f"✅ Trait data available: {len(original_traits)} traits")
                    print(f"   Traits: {list(original_traits.keys())}")
                    
                    # Test improvement calculations
                    improvements = {}
                    for trait in original_traits:
                        if trait in backstory_traits:
                            improvement = backstory_traits[trait] - original_traits[trait]
                            improvements[trait] = improvement
                    
                    print(f"✅ Improvement calculations work: {len(improvements)} improvements calculated")
                    
                    return True
                else:
                    print("❌ Missing trait averages data")
                    return False
            else:
                print("❌ Missing required Agora versions")
                return False
        else:
            print("❌ Missing likert evaluation data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing detailed analysis: {e}")
        return False

def test_elo_comparison_data():
    """Test that ELO comparison will display correctly."""
    print("\n🔍 Testing ELO Comparison component...")
    
    try:
        from agora_evaluation_dashboard import AgoraEvaluationDashboard
        
        # Create dashboard instance
        dashboard = AgoraEvaluationDashboard()
        
        # Find evaluation files
        files = dashboard.find_evaluation_files()
        if not files:
            print("❌ No evaluation files found")
            return False
        
        # Load evaluation summary
        first_file = files[0]
        summary = dashboard.load_evaluation_summary(first_file['path'])
        if not summary:
            print("❌ Could not load evaluation summary")
            return False
        
        # Test ELO data
        if 'elo_comparison' in summary:
            elo_data = summary['elo_comparison']
            
            if 'trait_wins' in elo_data:
                trait_wins = elo_data['trait_wins']
                print(f"✅ ELO trait wins data found: {len(trait_wins)} traits")
                
                # Test win chart data preparation
                traits = list(trait_wins.keys())
                original_wins = []
                backstory_wins = []
                
                for trait in traits:
                    wins = trait_wins[trait]
                    original_wins.append(wins.get('agora_original', 0))
                    backstory_wins.append(wins.get('agora_with_backstory', 0))
                
                print(f"✅ Win chart data prepared: {len(traits)} traits")
                print(f"   Original wins: {original_wins}")
                print(f"   Backstory wins: {backstory_wins}")
                
                # Test win percentage calculations
                for trait in traits:
                    wins = trait_wins[trait]
                    total_wins = sum(wins.values())
                    if total_wins > 0:
                        original_pct = (wins.get('agora_original', 0) / total_wins) * 100
                        backstory_pct = (wins.get('agora_with_backstory', 0) / total_wins) * 100
                        print(f"   {trait}: Original {original_pct:.1f}%, Backstory {backstory_pct:.1f}%")
                
                return True
            else:
                print("❌ Missing trait_wins in ELO data")
                return False
        else:
            print("❌ Missing ELO comparison data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ELO comparison: {e}")
        return False

def test_research_logging():
    """Test research logging functionality."""
    print("\n🔍 Testing Research Logging component...")
    
    try:
        from research_logger import get_research_logger
        
        # Get logger instance
        logger = get_research_logger()
        
        # Test logging different types of entries
        logger.log_prompt_test(
            prompt_type="character_card",
            prompt_version="agora_original",
            input_data={"prompt": "Test character card"},
            output_data={"response": "Test response"}
        )
        
        logger.log_api_call(
            endpoint="test_endpoint",
            prompt="Test prompt",
            response="Test response", 
            model="test_model",
            tokens_used=100,
            response_time=1.5
        )
        
        logger.log_evaluation_result(
            evaluation_type="likert",
            conversation_id="test_conv",
            judge_prompt="Test judge prompt",
            judge_response="Test judge response",
            scores={"Collaborative": 4.5, "Inquisitive": 4.0},
            reasoning="Test reasoning"
        )
        
        # Test log retrieval
        logs = logger.get_logs()
        if logs:
            print(f"✅ Research logging working: {len(logs)} log entries")
            
            # Check different log types
            log_types = set(log.get('type') for log in logs)
            print(f"   Log types: {log_types}")
            
            return True
        else:
            print("❌ No logs found after logging")
            return False
            
    except Exception as e:
        print(f"❌ Error testing research logging: {e}")
        return False

def test_prompt_display():
    """Test prompt display functionality."""
    print("\n🔍 Testing Prompt Display component...")
    
    try:
        from prompt_config import get_prompt_manager
        
        pm = get_prompt_manager()
        
        # Test character card retrieval
        agora_original = pm.get_character_card("agora_original")
        agora_backstory = pm.get_character_card("agora_with_backstory")
        
        if agora_original and agora_backstory:
            print("✅ Character cards retrieved successfully")
            print(f"   Original length: {len(agora_original)} characters")
            print(f"   Backstory length: {len(agora_backstory)} characters")
        else:
            print("❌ Failed to retrieve character cards")
            return False
        
        # Test scenario prompt
        scenario_prompt = pm.get_scenario_prompt(3)
        if scenario_prompt:
            print("✅ Scenario prompt retrieved successfully")
            print(f"   Scenario prompt length: {len(scenario_prompt)} characters")
        else:
            print("❌ Failed to retrieve scenario prompt")
            return False
        
        # Test judge prompts
        sample_conv = {
            'user_message': "Test message",
            'assistant_response': "Test response"
        }
        
        likert_prompt = pm.get_likert_prompt(sample_conv)
        if likert_prompt:
            print("✅ Likert judge prompt retrieved successfully")
        else:
            print("❌ Failed to retrieve Likert judge prompt")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing prompt display: {e}")
        return False

def main():
    """Main testing function."""
    print("🧪 TESTING DASHBOARD COMPONENTS")
    print("=" * 50)
    
    components = [
        ("Detailed Analysis", test_detailed_analysis_data),
        ("ELO Comparison", test_elo_comparison_data),
        ("Research Logging", test_research_logging),
        ("Prompt Display", test_prompt_display)
    ]
    
    passed = 0
    total = len(components)
    
    for name, test_func in components:
        try:
            if test_func():
                passed += 1
                print(f"✅ {name} component test passed")
            else:
                print(f"❌ {name} component test failed")
        except Exception as e:
            print(f"❌ {name} component test error: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 COMPONENT TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL COMPONENT TESTS PASSED!")
        print("\n📋 DASHBOARD SHOULD DISPLAY:")
        print("✅ Detailed Analysis: Radar charts, score tables, statistical analysis")
        print("✅ ELO Comparison: Win charts, trait tabs, percentages")
        print("✅ Research Logs: Session management, log entries, performance metrics")
        print("✅ Prompt Display: Character cards, scenario prompts, judge prompts")
    else:
        print("⚠️  Some component tests failed. Dashboard may not display correctly.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)