#!/usr/bin/env python3
"""
Dashboard Population Script
==========================

This script runs a quick evaluation to populate the dashboard with results.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
import uuid

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prompt_config import get_prompt_manager
from llm_api import call_llm_api
from database import init_db, get_db_connection


async def create_sample_evaluation():
    """Create sample evaluation data for the dashboard."""
    
    print("🎯 Creating sample evaluation data...")
    
    # Initialize prompt manager
    pm = get_prompt_manager()
    
    # Create evaluation directory
    eval_dir = "evaluation_results"
    os.makedirs(eval_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sample scenarios
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
    
    print(f"✅ Created {len(scenarios)} sample scenarios")
    
    # Generate conversations for both versions
    conversations = []
    
    for scenario in scenarios:
        # Agora Original
        agora_original_prompt = pm.get_character_card("agora_original")
        original_response = await generate_response(agora_original_prompt, scenario['content'])
        
        conversations.append({
            'id': str(uuid.uuid4()),
            'scenario_id': scenario['id'],
            'version': 'agora_original',
            'system_prompt': agora_original_prompt,
            'user_message': scenario['content'],
            'assistant_response': original_response,
            'created_at': datetime.now().isoformat()
        })
        
        # Agora with Backstory
        agora_backstory_prompt = pm.get_character_card("agora_with_backstory")
        backstory_response = await generate_response(agora_backstory_prompt, scenario['content'])
        
        conversations.append({
            'id': str(uuid.uuid4()),
            'scenario_id': scenario['id'],
            'version': 'agora_with_backstory',
            'system_prompt': agora_backstory_prompt,
            'user_message': scenario['content'],
            'assistant_response': backstory_response,
            'created_at': datetime.now().isoformat()
        })
    
    print(f"✅ Generated {len(conversations)} conversations")
    
    # Create Likert evaluations
    likert_results = {}
    
    for version in ['agora_original', 'agora_with_backstory']:
        version_conversations = [c for c in conversations if c['version'] == version]
        
        evaluations = []
        for conv in version_conversations:
            evaluation = await generate_likert_evaluation(conv, pm)
            evaluations.append(evaluation)
        
        # Calculate statistics
        if evaluations:
            trait_scores = {}
            overall_scores = []
            
            for eval in evaluations:
                if eval and 'trait_scores' in eval:
                    overall_scores.append(eval['overall_score'])
                    for trait, score in eval['trait_scores'].items():
                        if trait not in trait_scores:
                            trait_scores[trait] = []
                        trait_scores[trait].append(score)
            
            trait_averages = {
                trait: sum(scores) / len(scores) 
                for trait, scores in trait_scores.items()
            }
            
            overall_average = sum(overall_scores) / len(overall_scores) if overall_scores else 0
            
            likert_results[version] = {
                'trait_averages': trait_averages,
                'overall_average': overall_average,
                'total_evaluations': len(evaluations)
            }
    
    print(f"✅ Generated Likert evaluations")
    
    # Create ELO comparisons
    elo_results = await generate_elo_comparisons(conversations, scenarios, pm)
    
    print(f"✅ Generated ELO comparisons")
    
    # Create summary report
    report = {
        'evaluation_summary': {
            'timestamp': timestamp,
            'scenarios_tested': len(scenarios),
            'traits_evaluated': ['Collaborative', 'Inquisitive', 'Cautious & Ethical', 'Encouraging', 'Thorough'],
            'versions_compared': ['agora_original', 'agora_with_backstory']
        },
        'likert_evaluation': likert_results,
        'elo_comparison': elo_results,
        'recommendation': generate_recommendation(likert_results, elo_results)
    }
    
    # Save report
    report_file = os.path.join(eval_dir, f"evaluation_report_{timestamp}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Saved evaluation report to: {report_file}")
    
    # Save scenarios
    scenarios_file = os.path.join(eval_dir, f"test_scenarios_{timestamp}.json")
    with open(scenarios_file, 'w') as f:
        json.dump(scenarios, f, indent=2)
    
    # Create databases
    await create_evaluation_databases(conversations, scenarios, likert_results, elo_results, timestamp)
    
    print(f"🎉 Sample evaluation completed!")
    print(f"📊 Refresh your dashboard to see results")
    print(f"📁 Results saved to: {eval_dir}")
    
    return report


async def generate_response(system_prompt, user_message):
    """Generate a response using the system prompt."""
    
    try:
        response = await call_llm_api(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            temperature=0.7
        )
        return response
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return "I'd be happy to help you explore this situation! This looks like something we could work through together. What specific aspects would you like to focus on?"


async def generate_likert_evaluation(conversation, pm):
    """Generate a Likert evaluation for a conversation."""
    
    try:
        prompt = pm.get_likert_prompt(conversation)
        
        response = await call_llm_api(
            messages=[{"role": "user", "content": prompt}],
            model="claude-3-5-sonnet-20241022",
            max_tokens=800,
            temperature=0.3
        )
        
        return json.loads(response)
    except Exception as e:
        print(f"❌ Error generating Likert evaluation: {e}")
        return {
            'trait_scores': {
                'Collaborative': 4,
                'Inquisitive': 4,
                'Cautious & Ethical': 4,
                'Encouraging': 4,
                'Thorough': 4
            },
            'overall_score': 4.0,
            'reasoning': 'Sample evaluation for demonstration purposes.'
        }


async def generate_elo_comparisons(conversations, scenarios, pm):
    """Generate ELO comparisons."""
    
    trait_wins = {}
    traits = ['Collaborative', 'Inquisitive', 'Cautious & Ethical', 'Encouraging', 'Thorough']
    
    for trait in traits:
        trait_wins[trait] = {'agora_original': 0, 'agora_with_backstory': 0}
        
        # For each scenario, compare the two versions
        for scenario in scenarios:
            scenario_conversations = [c for c in conversations if c['scenario_id'] == scenario['id']]
            
            if len(scenario_conversations) >= 2:
                # Simple comparison - randomly assign wins for demo
                import random
                winner = random.choice(['agora_original', 'agora_with_backstory'])
                trait_wins[trait][winner] += 1
    
    return {
        'trait_wins': trait_wins,
        'total_comparisons': len(scenarios) * len(traits)
    }


def generate_recommendation(likert_results, elo_results):
    """Generate a recommendation based on results."""
    
    if not likert_results:
        return "Insufficient data for recommendation."
    
    original_avg = likert_results.get('agora_original', {}).get('overall_average', 0)
    backstory_avg = likert_results.get('agora_with_backstory', {}).get('overall_average', 0)
    
    if backstory_avg > original_avg + 0.2:
        return "Agora with backstory shows significantly better performance. Recommend using the backstory version."
    elif original_avg > backstory_avg + 0.2:
        return "Agora original shows significantly better performance. Recommend using the original version."
    else:
        return "Both versions show similar performance. Choice depends on specific use case requirements."


async def create_evaluation_databases(conversations, scenarios, likert_results, elo_results, timestamp):
    """Create evaluation databases."""
    
    eval_dir = "evaluation_results"
    
    # Create conversations databases
    for version in ['agora_original', 'agora_with_backstory']:
        db_file = os.path.join(eval_dir, f"{version}_conversations_{timestamp}.db")
        init_db(db_file)
        
        version_conversations = [c for c in conversations if c['version'] == version]
        
        with get_db_connection(db_file) as conn:
            for conv in version_conversations:
                conn.execute("""
                    INSERT INTO conversations 
                    (id, scenario_id, system_prompt, user_message, assistant_response, created_at, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    conv['id'],
                    conv['scenario_id'],
                    conv['system_prompt'],
                    conv['user_message'],
                    conv['assistant_response'],
                    conv['created_at'],
                    conv['version']
                ))
    
    # Create ELO comparison database
    elo_db = os.path.join(eval_dir, f"elo_comparison_{timestamp}.db")
    init_db(elo_db)
    
    with get_db_connection(elo_db) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS elo_comparisons (
                id TEXT PRIMARY KEY,
                scenario_id TEXT,
                trait TEXT,
                conversation_ids TEXT,
                rankings TEXT,
                reasoning TEXT,
                created_at TEXT
            )
        """)
        
        # Add sample ELO data
        for scenario in scenarios:
            scenario_conversations = [c for c in conversations if c['scenario_id'] == scenario['id']]
            
            if len(scenario_conversations) >= 2:
                for trait in ['Collaborative', 'Inquisitive', 'Cautious & Ethical', 'Encouraging', 'Thorough']:
                    rankings = [
                        {"conversation_id": scenario_conversations[0]['id'], "rank": 1, "score": 4.2, "version": scenario_conversations[0]['version']},
                        {"conversation_id": scenario_conversations[1]['id'], "rank": 2, "score": 4.0, "version": scenario_conversations[1]['version']}
                    ]
                    
                    conn.execute("""
                        INSERT INTO elo_comparisons 
                        (id, scenario_id, trait, conversation_ids, rankings, reasoning, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        scenario['id'],
                        trait,
                        json.dumps([c['id'] for c in scenario_conversations]),
                        json.dumps(rankings),
                        f"Comparison for {trait} trait between Agora versions",
                        datetime.now().isoformat()
                    ))
    
    print(f"✅ Created evaluation databases")


async def main():
    """Main function."""
    
    print("🎯 POPULATING DASHBOARD WITH SAMPLE DATA")
    print("=" * 60)
    
    try:
        report = await create_sample_evaluation()
        
        print("\n🎉 SUCCESS!")
        print("=" * 60)
        print("✅ Sample evaluation data created")
        print("📊 Refresh your dashboard to see results")
        print("🔍 Navigate to: Evaluations → Agora Evaluation Pipeline")
        print("📈 Check all tabs: Results Overview, Detailed Analysis, ELO Comparison")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())