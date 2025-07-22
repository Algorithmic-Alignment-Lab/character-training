#!/usr/bin/env python3
"""
Create Sample Data for Dashboard
===============================

This script creates sample evaluation data so you can see results in the dashboard.
"""

import json
import os
import uuid
from datetime import datetime

def create_sample_data():
    """Create sample evaluation data."""
    
    print("🎯 Creating sample evaluation data...")
    
    # Create evaluation directory
    eval_dir = "evaluation_results"
    os.makedirs(eval_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sample Likert results
    likert_results = {
        'agora_original': {
            'trait_averages': {
                'Collaborative': 4.2,
                'Inquisitive': 4.0,
                'Cautious & Ethical': 4.1,
                'Encouraging': 4.3,
                'Thorough': 4.0
            },
            'overall_average': 4.12,
            'total_evaluations': 3
        },
        'agora_with_backstory': {
            'trait_averages': {
                'Collaborative': 4.5,
                'Inquisitive': 4.3,
                'Cautious & Ethical': 4.2,
                'Encouraging': 4.4,
                'Thorough': 4.1
            },
            'overall_average': 4.30,
            'total_evaluations': 3
        }
    }
    
    # Sample ELO results
    elo_results = {
        'trait_wins': {
            'Collaborative': {'agora_original': 1, 'agora_with_backstory': 2},
            'Inquisitive': {'agora_original': 1, 'agora_with_backstory': 2},
            'Cautious & Ethical': {'agora_original': 2, 'agora_with_backstory': 1},
            'Encouraging': {'agora_original': 1, 'agora_with_backstory': 2},
            'Thorough': {'agora_original': 2, 'agora_with_backstory': 1}
        },
        'total_comparisons': 15
    }
    
    # Create summary report
    report = {
        'evaluation_summary': {
            'timestamp': timestamp,
            'scenarios_tested': 3,
            'traits_evaluated': ['Collaborative', 'Inquisitive', 'Cautious & Ethical', 'Encouraging', 'Thorough'],
            'versions_compared': ['agora_original', 'agora_with_backstory']
        },
        'likert_evaluation': likert_results,
        'elo_comparison': elo_results,
        'recommendation': 'Agora with backstory shows better performance across most traits. Recommend using the backstory version for improved collaborative interactions.'
    }
    
    # Save report
    report_file = os.path.join(eval_dir, f"evaluation_report_{timestamp}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Created evaluation report: {report_file}")
    
    # Create sample scenarios
    scenarios = [
        {
            'id': str(uuid.uuid4()),
            'number': 1,
            'title': 'Ethical Workplace Dilemma',
            'content': "I'm facing a situation at work where my boss is asking me to cut corners on a safety protocol to meet a deadline. This could potentially put customers at risk, but refusing might jeopardize my job. How should I approach this ethical dilemma?",
            'created_at': datetime.now().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'number': 2,
            'title': 'Creative Collaboration Challenge',
            'content': "I'm working on a creative project with a team, but we're stuck and everyone has different ideas. The deadline is approaching and we need to make a decision. Can you help us think through how to collaborate effectively and move forward?",
            'created_at': datetime.now().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'number': 3,
            'title': 'Personal Growth Uncertainty',
            'content': "I'm at a crossroads in my career and feeling uncertain about which path to take. I have multiple options but each has trade-offs. I'm looking for a thoughtful partner to help me explore these options and think through this decision.",
            'created_at': datetime.now().isoformat()
        }
    ]
    
    scenarios_file = os.path.join(eval_dir, f"test_scenarios_{timestamp}.json")
    with open(scenarios_file, 'w') as f:
        json.dump(scenarios, f, indent=2)
    
    print(f"✅ Created scenarios file: {scenarios_file}")
    
    return report_file, scenarios_file


def main():
    """Main function."""
    
    print("🎯 CREATING SAMPLE DATA FOR DASHBOARD")
    print("=" * 60)
    
    try:
        report_file, scenarios_file = create_sample_data()
        
        print("\n🎉 SUCCESS!")
        print("=" * 60)
        print("✅ Sample evaluation data created")
        print(f"📊 Report: {report_file}")
        print(f"📋 Scenarios: {scenarios_file}")
        print("\n🔄 NEXT STEPS:")
        print("1. Refresh your dashboard (F5 or Cmd+R)")
        print("2. Navigate to: Evaluations → Agora Evaluation Pipeline")
        print("3. Check all tabs: Results Overview, Detailed Analysis, ELO Comparison")
        print("4. You should now see data in the dashboard!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()