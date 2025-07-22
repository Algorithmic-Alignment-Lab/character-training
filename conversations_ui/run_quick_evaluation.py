#!/usr/bin/env python3
"""
Quick Evaluation Runner
======================

This script runs a quick evaluation between Agora versions and shows all prompts used.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_agora_evaluation_pipeline import AgoraEvaluationPipeline
from prompt_config import get_prompt_manager


async def run_quick_evaluation_with_prompt_display():
    """Run a quick evaluation and display all prompts used."""
    
    print("🎯 QUICK AGORA EVALUATION WITH PROMPT DISPLAY")
    print("=" * 60)
    
    # Initialize prompt manager
    pm = get_prompt_manager()
    
    # Display all prompts that will be used
    print("\n📋 PROMPTS THAT WILL BE USED:")
    print("=" * 60)
    
    print("\n1. 🎭 CHARACTER CARD PROMPTS:")
    print("-" * 40)
    
    print("\n📝 Agora Original:")
    agora_original = pm.get_character_card("agora_original")
    print(f"Length: {len(agora_original)} characters")
    print(f"Preview: {agora_original[:200]}...")
    
    print("\n📝 Agora with Backstory:")
    agora_backstory = pm.get_character_card("agora_with_backstory")
    print(f"Length: {len(agora_backstory)} characters")
    print(f"Preview: {agora_backstory[:200]}...")
    
    print("\n2. 🎯 SCENARIO GENERATION PROMPT:")
    print("-" * 40)
    scenario_prompt = pm.get_scenario_prompt(3)
    print(f"Length: {len(scenario_prompt)} characters")
    print(f"Preview: {scenario_prompt[:300]}...")
    
    print("\n3. ⚖️ JUDGE PROMPTS:")
    print("-" * 40)
    
    # Sample conversation for judge prompt display
    sample_conversation = {
        'system_prompt': agora_original[:100],
        'user_message': "I'm facing an ethical dilemma at work. Can you help me think through this?",
        'assistant_response': "I'd be happy to help you work through this ethical dilemma! Let's explore this together. Can you tell me more about the specific situation you're facing? Understanding the details will help us consider different perspectives and work toward a thoughtful approach."
    }
    
    print("\n📝 Likert Scale Judge:")
    likert_prompt = pm.get_likert_prompt(sample_conversation)
    print(f"Length: {len(likert_prompt)} characters")
    print(f"Preview: {likert_prompt[:300]}...")
    
    print("\n📝 ELO Comparison Judge:")
    sample_formatted_convs = "**Conversation A (agora_original):**\nUser: Test\nAssistant: Test response"
    elo_prompt = pm.get_elo_prompt(sample_formatted_convs, "Collaborative")
    print(f"Length: {len(elo_prompt)} characters")
    print(f"Preview: {elo_prompt[:300]}...")
    
    print("\n🚀 RUNNING EVALUATION:")
    print("=" * 60)
    
    # Run the evaluation with 3 scenarios for quick demo
    pipeline = AgoraEvaluationPipeline(
        scenarios_count=3,
        output_dir="evaluation_results"
    )
    
    print("Starting evaluation pipeline...")
    results = await pipeline.run_complete_pipeline()
    
    if results:
        print("\n🎉 EVALUATION COMPLETED!")
        print("=" * 60)
        
        # Show key results
        if 'report' in results:
            report = results['report']
            
            print("\n📊 QUICK RESULTS:")
            print(f"Scenarios tested: {len(results['scenarios'])}")
            print(f"Conversations generated: {len(results['conversations'])}")
            print(f"Likert evaluations: {len(results['likert_results'])}")
            print(f"ELO comparisons: Available")
            
            # Show Likert results if available
            if 'likert_evaluation' in report:
                print("\n📈 LIKERT RESULTS:")
                for version, data in report['likert_evaluation'].items():
                    if 'overall_average' in data:
                        print(f"  {version}: {data['overall_average']:.2f}/5.0")
            
            # Show recommendation
            if 'recommendation' in report:
                print(f"\n💡 RECOMMENDATION:")
                print(f"  {report['recommendation']}")
        
        print(f"\n📁 Results saved to: {pipeline.output_dir}")
        print(f"🖥️  Refresh the dashboard to see results!")
        print(f"📊 Navigate to: Evaluations → Agora Evaluation Pipeline")
        
        return True
    else:
        print("\n❌ Evaluation failed!")
        return False


def show_prompt_locations():
    """Show where users can find and edit prompts."""
    
    print("\n🔧 WHERE TO EDIT PROMPTS:")
    print("=" * 60)
    
    print("\n1. 🎭 Character Cards:")
    print("   Location: prompt_config.py → character_cards section")
    print("   Dashboard: Prompt Testing → Character Cards")
    print("   Variables: agora_original, agora_with_backstory")
    
    print("\n2. 🎯 Scenario Generation:")
    print("   Location: prompt_config.py → scenario_generation section")
    print("   Dashboard: Prompt Testing → Scenario Generation")
    print("   Template: Uses {scenarios_count} placeholder")
    
    print("\n3. ⚖️ Judge Prompts:")
    print("   Location: prompt_config.py → evaluation_judges section")
    print("   Dashboard: Prompt Testing → Judge Prompts")
    print("   Types: likert_evaluator, elo_comparator, enhanced_likert_evaluator")
    
    print("\n4. 📝 Trait Definitions:")
    print("   Location: prompt_config.py → trait_definitions section")
    print("   Traits: Collaborative, Inquisitive, Cautious & Ethical, Encouraging, Thorough")
    
    print("\n🛠️  TESTING PROMPTS:")
    print("   1. Go to 'Prompt Testing' tab in dashboard")
    print("   2. Edit any prompt in the text area")
    print("   3. Click 'Test Prompt' to see results")
    print("   4. Compare different versions")
    print("   5. Save changes when satisfied")


def main():
    """Main function."""
    
    print("🎯 Starting quick evaluation with prompt display...")
    
    # Show prompt locations first
    show_prompt_locations()
    
    # Ask user if they want to proceed
    print("\n" + "=" * 60)
    response = input("🚀 Run evaluation now? This will take 2-3 minutes. (y/N): ").lower()
    
    if response == 'y':
        # Run the evaluation
        success = asyncio.run(run_quick_evaluation_with_prompt_display())
        
        if success:
            print("\n✅ Done! Refresh your dashboard to see results.")
        else:
            print("\n❌ Evaluation failed. Check error messages above.")
    else:
        print("\n📋 Evaluation skipped.")
        print("💡 Run 'python run_quick_evaluation.py' when ready.")
        print("🖥️  Or use the dashboard: Evaluations → Run Pipeline")


if __name__ == "__main__":
    main()