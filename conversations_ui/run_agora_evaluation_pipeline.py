#!/usr/bin/env python3
"""
Agora Evaluation Pipeline
========================

This script runs the complete evaluation pipeline for both Agora versions:
1. Agora without backstory (original)
2. Agora with backstory (extended)

It generates synthetic conversations, evaluates them using both ELO and Likert 
rating systems, and creates comprehensive evaluation reports.

Usage:
    python run_agora_evaluation_pipeline.py --scenarios 50 --output evaluation_results
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import sqlite3
import uuid

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_api import call_llm_api
from generate_conversations import ConversationGenerator
from judge_conversations import ConversationJudge
from database import init_db, get_db_connection
from prompt_config import get_prompt_manager


class AgoraEvaluationPipeline:
    """
    Complete evaluation pipeline for Agora persona comparison.
    
    This pipeline:
    1. Generates synthetic scenarios for testing collaborative traits
    2. Creates conversations using both Agora versions
    3. Evaluates conversations using ELO and Likert rating systems
    4. Generates comprehensive comparison reports
    """
    
    def __init__(self, scenarios_count: int = 50, output_dir: str = "evaluation_results"):
        self.scenarios_count = scenarios_count
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize prompt manager
        self.prompt_manager = get_prompt_manager()
        
        # Get character prompts from centralized config
        self.agora_original = self.prompt_manager.get_character_card("agora_original")
        self.agora_with_backstory = self.prompt_manager.get_character_card("agora_with_backstory")
        
        # Evaluation traits
        self.traits = [
            "Collaborative",
            "Inquisitive", 
            "Cautious & Ethical",
            "Encouraging",
            "Thorough"
        ]
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize judge
        self.judge = ConversationJudge(judge_model="claude-3-5-sonnet-20241022")
        
        print(f"🚀 AGORA EVALUATION PIPELINE INITIALIZED")
        print(f"📊 Scenarios to generate: {self.scenarios_count}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🕒 Timestamp: {self.timestamp}")
        print("="*60)
    
    async def generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """Generate diverse test scenarios for collaborative AI evaluation."""
        
        print(f"🎯 Generating {self.scenarios_count} test scenarios...")
        
        prompt = self.prompt_manager.get_scenario_prompt(self.scenarios_count)
        
        try:
            response = await call_llm_api(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.7
            )
            
            scenarios = self.parse_scenarios(response)
            
            # Save scenarios to file
            scenarios_file = os.path.join(self.output_dir, f"test_scenarios_{self.timestamp}.json")
            with open(scenarios_file, 'w') as f:
                json.dump(scenarios, f, indent=2)
            
            print(f"✅ Generated {len(scenarios)} test scenarios")
            print(f"💾 Saved to: {scenarios_file}")
            
            return scenarios
            
        except Exception as e:
            print(f"❌ Error generating scenarios: {e}")
            return []
    
    def parse_scenarios(self, response: str) -> List[Dict[str, Any]]:
        """Parse scenarios from LLM response."""
        scenarios = []
        sections = response.split("**SCENARIO")
        
        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            if section.strip():
                lines = section.strip().split('\n')
                title_line = lines[0] if lines else f"{i}: Test Scenario"
                
                # Extract title (everything after the number and colon)
                if ':' in title_line:
                    title = title_line.split(':', 1)[1].strip().rstrip('**')
                else:
                    title = f"Test Scenario {i}"
                
                # Get content (skip title line and separators)
                content_lines = []
                for line in lines[1:]:
                    if line.strip() == '---':
                        break
                    content_lines.append(line)
                
                content = '\n'.join(content_lines).strip()
                
                if content:
                    scenario = {
                        'id': str(uuid.uuid4()),
                        'number': i,
                        'title': title,
                        'content': content,
                        'created_at': datetime.now().isoformat()
                    }
                    scenarios.append(scenario)
        
        return scenarios
    
    async def generate_conversations(self, scenarios: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate conversations using both Agora versions."""
        
        print(f"🗣️  Generating conversations for both Agora versions...")
        
        db_files = {}
        
        # Generate conversations for each version
        for version_name, system_prompt in [
            ("agora_original", self.agora_original),
            ("agora_with_backstory", self.agora_with_backstory)
        ]:
            print(f"  📝 Generating conversations for {version_name}...")
            
            db_file = os.path.join(self.output_dir, f"{version_name}_conversations_{self.timestamp}.db")
            db_files[version_name] = db_file
            
            # Initialize database
            init_db(db_file)
            
            # Generate conversations
            conversations = []
            for i, scenario in enumerate(scenarios):
                print(f"    [{i+1}/{len(scenarios)}] Processing: {scenario['title'][:50]}...")
                
                # Create conversation
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": scenario['content']}
                ]
                
                try:
                    response = await call_llm_api(
                        messages=messages,
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=800,
                        temperature=0.7
                    )
                    
                    conversation = {
                        'id': str(uuid.uuid4()),
                        'scenario_id': scenario['id'],
                        'system_prompt': system_prompt,
                        'user_message': scenario['content'],
                        'assistant_response': response,
                        'created_at': datetime.now().isoformat(),
                        'version': version_name
                    }
                    
                    conversations.append(conversation)
                    
                    # Save to database
                    with get_db_connection(db_file) as conn:
                        conn.execute("""
                            INSERT INTO conversations 
                            (id, scenario_id, system_prompt, user_message, assistant_response, created_at, version)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            conversation['id'],
                            conversation['scenario_id'],
                            conversation['system_prompt'],
                            conversation['user_message'],
                            conversation['assistant_response'],
                            conversation['created_at'],
                            conversation['version']
                        ))
                    
                    # Add delay to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"    ❌ Error generating conversation: {e}")
                    continue
            
            print(f"  ✅ Generated {len(conversations)} conversations for {version_name}")
        
        return db_files
    
    async def run_likert_evaluation(self, db_files: Dict[str, str]) -> Dict[str, str]:
        """Run Likert scale evaluation for all conversations."""
        
        print(f"📊 Running Likert scale evaluation...")
        
        evaluation_results = {}
        
        for version_name, db_file in db_files.items():
            print(f"  🔍 Evaluating {version_name}...")
            
            # Create evaluation database
            eval_db = os.path.join(self.output_dir, f"{version_name}_likert_evaluation_{self.timestamp}.db")
            evaluation_results[version_name] = eval_db
            
            # Initialize evaluation database
            self.init_evaluation_db(eval_db)
            
            # Load conversations
            conversations = self.load_conversations(db_file)
            
            # Evaluate each conversation
            for i, conversation in enumerate(conversations):
                print(f"    [{i+1}/{len(conversations)}] Evaluating conversation {conversation['id'][:8]}...")
                
                # Generate Likert evaluation
                evaluation = await self.generate_likert_evaluation(conversation)
                
                if evaluation:
                    # Save evaluation
                    with get_db_connection(eval_db) as conn:
                        conn.execute("""
                            INSERT INTO likert_evaluations 
                            (id, conversation_id, trait_scores, overall_score, reasoning, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            str(uuid.uuid4()),
                            conversation['id'],
                            json.dumps(evaluation['trait_scores']),
                            evaluation['overall_score'],
                            evaluation['reasoning'],
                            datetime.now().isoformat()
                        ))
                
                await asyncio.sleep(1)  # Rate limiting
            
            print(f"  ✅ Completed Likert evaluation for {version_name}")
        
        return evaluation_results
    
    async def run_elo_evaluation(self, db_files: Dict[str, str]) -> str:
        """Run ELO comparison evaluation between both versions."""
        
        print(f"🏆 Running ELO comparison evaluation...")
        
        # Create ELO evaluation database
        elo_db = os.path.join(self.output_dir, f"elo_comparison_{self.timestamp}.db")
        self.init_elo_db(elo_db)
        
        # Load conversations from both versions
        all_conversations = []
        for version_name, db_file in db_files.items():
            conversations = self.load_conversations(db_file)
            for conv in conversations:
                conv['version'] = version_name
            all_conversations.extend(conversations)
        
        # Group conversations by scenario for fair comparison
        scenario_groups = {}
        for conv in all_conversations:
            scenario_id = conv['scenario_id']
            if scenario_id not in scenario_groups:
                scenario_groups[scenario_id] = []
            scenario_groups[scenario_id].append(conv)
        
        # Run ELO comparisons for each trait
        for trait in self.traits:
            print(f"  ⚖️  Evaluating {trait}...")
            
            trait_comparisons = []
            
            # Compare conversations for each scenario
            for scenario_id, conversations in scenario_groups.items():
                if len(conversations) >= 2:  # Need at least 2 conversations to compare
                    
                    comparison = await self.generate_elo_comparison(conversations, trait)
                    
                    if comparison:
                        trait_comparisons.append(comparison)
                        
                        # Save comparison
                        with get_db_connection(elo_db) as conn:
                            conn.execute("""
                                INSERT INTO elo_comparisons 
                                (id, scenario_id, trait, conversation_ids, rankings, reasoning, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                str(uuid.uuid4()),
                                scenario_id,
                                trait,
                                json.dumps([c['id'] for c in conversations]),
                                json.dumps(comparison['rankings']),
                                comparison['reasoning'],
                                datetime.now().isoformat()
                            ))
                    
                    await asyncio.sleep(1)  # Rate limiting
            
            print(f"  ✅ Completed {len(trait_comparisons)} comparisons for {trait}")
        
        return elo_db
    
    async def generate_likert_evaluation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Likert scale evaluation for a single conversation."""
        
        prompt = self.prompt_manager.get_likert_prompt(conversation)
        
        try:
            response = await call_llm_api(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.3
            )
            
            # Parse JSON response
            evaluation = json.loads(response)
            return evaluation
            
        except Exception as e:
            print(f"    ❌ Error in Likert evaluation: {e}")
            return None
    
    async def generate_elo_comparison(self, conversations: List[Dict[str, Any]], trait: str) -> Dict[str, Any]:
        """Generate ELO comparison between conversations for a specific trait."""
        
        # Format conversations for comparison
        formatted_convs = []
        for i, conv in enumerate(conversations):
            formatted_convs.append(f"""
**Conversation {chr(65+i)} ({conv['version']}):**
User: {conv['user_message']}
Assistant: {conv['assistant_response']}
""")
        
        prompt = self.prompt_manager.get_elo_prompt(chr(10).join(formatted_convs), trait)
        
        try:
            response = await call_llm_api(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.3
            )
            
            comparison = json.loads(response)
            
            # Map rankings back to conversation IDs
            for i, ranking in enumerate(comparison['rankings']):
                if i < len(conversations):
                    ranking['conversation_id'] = conversations[i]['id']
                    ranking['version'] = conversations[i]['version']
            
            return comparison
            
        except Exception as e:
            print(f"    ❌ Error in ELO comparison: {e}")
            return None
    
    def init_evaluation_db(self, db_file: str):
        """Initialize evaluation database."""
        with get_db_connection(db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS likert_evaluations (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    trait_scores TEXT,
                    overall_score REAL,
                    reasoning TEXT,
                    created_at TEXT
                )
            """)
    
    def init_elo_db(self, db_file: str):
        """Initialize ELO database.""" 
        with get_db_connection(db_file) as conn:
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
    
    def load_conversations(self, db_file: str) -> List[Dict[str, Any]]:
        """Load conversations from database."""
        conversations = []
        with get_db_connection(db_file) as conn:
            cursor = conn.execute("""
                SELECT id, scenario_id, system_prompt, user_message, assistant_response, created_at, version
                FROM conversations
            """)
            for row in cursor:
                conversations.append({
                    'id': row[0],
                    'scenario_id': row[1],
                    'system_prompt': row[2],
                    'user_message': row[3],
                    'assistant_response': row[4],
                    'created_at': row[5],
                    'version': row[6] if len(row) > 6 else 'unknown'
                })
        return conversations
    
    async def generate_summary_report(self, db_files: Dict[str, str], likert_results: Dict[str, str], elo_results: str):
        """Generate comprehensive summary report."""
        
        print(f"📋 Generating comprehensive summary report...")
        
        # Calculate statistics from Likert evaluations
        likert_stats = {}
        for version_name, eval_db in likert_results.items():
            stats = self.calculate_likert_stats(eval_db)
            likert_stats[version_name] = stats
        
        # Calculate ELO statistics
        elo_stats = self.calculate_elo_stats(elo_results)
        
        # Generate report
        report = {
            'evaluation_summary': {
                'timestamp': self.timestamp,
                'scenarios_tested': self.scenarios_count,
                'traits_evaluated': self.traits,
                'versions_compared': list(db_files.keys())
            },
            'likert_evaluation': likert_stats,
            'elo_comparison': elo_stats,
            'recommendation': self.generate_recommendation(likert_stats, elo_stats)
        }
        
        # Save report
        report_file = os.path.join(self.output_dir, f"evaluation_report_{self.timestamp}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Summary report saved to: {report_file}")
        return report
    
    def calculate_likert_stats(self, eval_db: str) -> Dict[str, Any]:
        """Calculate Likert evaluation statistics."""
        stats = {}
        
        with get_db_connection(eval_db) as conn:
            # Get all evaluations
            cursor = conn.execute("SELECT trait_scores, overall_score FROM likert_evaluations")
            evaluations = cursor.fetchall()
            
            if evaluations:
                trait_scores = {}
                overall_scores = []
                
                for trait_scores_json, overall_score in evaluations:
                    trait_data = json.loads(trait_scores_json)
                    overall_scores.append(overall_score)
                    
                    for trait, score in trait_data.items():
                        if trait not in trait_scores:
                            trait_scores[trait] = []
                        trait_scores[trait].append(score)
                
                # Calculate averages
                stats['trait_averages'] = {
                    trait: sum(scores) / len(scores) 
                    for trait, scores in trait_scores.items()
                }
                stats['overall_average'] = sum(overall_scores) / len(overall_scores)
                stats['total_evaluations'] = len(evaluations)
        
        return stats
    
    def calculate_elo_stats(self, elo_db: str) -> Dict[str, Any]:
        """Calculate ELO comparison statistics."""
        stats = {}
        
        with get_db_connection(elo_db) as conn:
            # Get all comparisons
            cursor = conn.execute("SELECT trait, rankings FROM elo_comparisons")
            comparisons = cursor.fetchall()
            
            if comparisons:
                trait_wins = {}
                
                for trait, rankings_json in comparisons:
                    rankings = json.loads(rankings_json)
                    
                    if trait not in trait_wins:
                        trait_wins[trait] = {'agora_original': 0, 'agora_with_backstory': 0}
                    
                    # Count wins (rank 1 = win)
                    for ranking in rankings:
                        if ranking['rank'] == 1:
                            version = ranking.get('version', 'unknown')
                            if version in trait_wins[trait]:
                                trait_wins[trait][version] += 1
                
                stats['trait_wins'] = trait_wins
                stats['total_comparisons'] = len(comparisons)
        
        return stats
    
    def generate_recommendation(self, likert_stats: Dict[str, Any], elo_stats: Dict[str, Any]) -> str:
        """Generate recommendation based on evaluation results."""
        
        # Simple recommendation logic
        if not likert_stats or not elo_stats:
            return "Insufficient data for recommendation."
        
        # Compare overall averages
        original_avg = likert_stats.get('agora_original', {}).get('overall_average', 0)
        backstory_avg = likert_stats.get('agora_with_backstory', {}).get('overall_average', 0)
        
        if backstory_avg > original_avg + 0.2:
            return "Agora with backstory shows significantly better performance. Recommend using the backstory version."
        elif original_avg > backstory_avg + 0.2:
            return "Agora original shows significantly better performance. Recommend using the original version."
        else:
            return "Both versions show similar performance. Choice depends on specific use case requirements."
    
    async def run_complete_pipeline(self):
        """Run the complete evaluation pipeline."""
        
        print(f"🚀 STARTING COMPLETE AGORA EVALUATION PIPELINE")
        print("="*60)
        
        try:
            # Step 1: Generate test scenarios
            scenarios = await self.generate_test_scenarios()
            if not scenarios:
                print("❌ Failed to generate scenarios. Exiting.")
                return
            
            # Step 2: Generate conversations
            db_files = await self.generate_conversations(scenarios)
            if not db_files:
                print("❌ Failed to generate conversations. Exiting.")
                return
            
            # Step 3: Run Likert evaluation
            likert_results = await self.run_likert_evaluation(db_files)
            
            # Step 4: Run ELO evaluation
            elo_results = await self.run_elo_evaluation(db_files)
            
            # Step 5: Generate summary report
            report = await self.generate_summary_report(db_files, likert_results, elo_results)
            
            print(f"🎉 EVALUATION PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"📊 Results saved to: {self.output_dir}")
            print(f"📋 Summary report: evaluation_report_{self.timestamp}.json")
            print("="*60)
            
            return {
                'scenarios': scenarios,
                'conversations': db_files,
                'likert_results': likert_results,
                'elo_results': elo_results,
                'report': report
            }
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            return None


async def main():
    parser = argparse.ArgumentParser(description="Run Agora evaluation pipeline")
    parser.add_argument("--scenarios", type=int, default=50, help="Number of test scenarios to generate")
    parser.add_argument("--output", default="evaluation_results", help="Output directory")
    
    args = parser.parse_args()
    
    # Create and run pipeline
    pipeline = AgoraEvaluationPipeline(
        scenarios_count=args.scenarios,
        output_dir=args.output
    )
    
    results = await pipeline.run_complete_pipeline()
    
    if results:
        print(f"\n✅ Pipeline completed successfully!")
        print(f"📁 Results in: {pipeline.output_dir}")
    else:
        print(f"\n❌ Pipeline failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())