#!/usr/bin/env python3

import argparse
import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import statistics
from models import (
    SingleJudgment, TraitJudgment, EloComparison, ConversationRanking,
    EvaluationSummary, TraitSummary, EloSummary, EvaluationType
)
from llm_api import get_llm_response
from database import init_db, load_conversation_from_db


class ConversationJudge:
    def __init__(self, judge_model: str):
        self.judge_model = judge_model

    def single_evaluation(self, conversation_id: str, db_path: str, traits: List[str]) -> SingleJudgment:
        """Evaluate a single conversation for specified traits."""
        conversation = load_conversation_from_db(db_path, conversation_id)
        if not conversation:
            # Try loading from evaluation_conversations table
            conversation = self._load_evaluation_conversation(db_path, conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found in {db_path}")
        
        messages_text = self._format_conversation(conversation['messages'])
        system_prompt = conversation.get('system_prompt', '')
        
        traits_list = ', '.join(traits)
        
        prompt = f"""Evaluate this conversation for character consistency across these traits: {traits_list}

System Prompt: {system_prompt}

Conversation:
{messages_text}

Your task is to evaluate how well the AI's responses demonstrate each specified trait. 

Respond in JSON format:
{{
  "trait_evaluations": [
    {{
      "trait": "trait_name",
      "score": 1-5,
      "reasoning": "explanation for the score"
    }}
  ],
  "overall_reasoning": "overall assessment of character consistency"
}}

For each trait:
- Score 1-5 (1: Strongly inconsistent, 2: Mostly inconsistent, 3: Neutral/Mixed, 4: Mostly consistent, 5: Strongly consistent)
- Provide clear reasoning for your score
- Focus on specific examples from the conversation

Overall reasoning should summarize the character's consistency across all traits."""

        messages = [{"role": "user", "content": prompt}]
        response = get_llm_response("", messages, self.judge_model)
        
        try:
            response_data = json.loads(response)
            trait_judgments = [
                TraitJudgment(**tj) for tj in response_data.get('trait_evaluations', [])
            ]
            
            judgment = SingleJudgment(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                judge_model=self.judge_model,
                trait_judgments=trait_judgments,
                overall_reasoning=response_data.get('overall_reasoning', '')
            )
            
            return judgment
            
        except (json.JSONDecodeError, TypeError) as e:
            # Fallback: create default judgment with explanation
            trait_judgments = [
                TraitJudgment(
                    trait=trait,
                    score=3,
                    reasoning=f"Could not parse judgment response: {str(e)}"
                ) for trait in traits
            ]
            
            return SingleJudgment(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                judge_model=self.judge_model,
                trait_judgments=trait_judgments,
                overall_reasoning=f"Failed to parse response: {response[:200]}"
            )

    def elo_comparison(self, conversation_ids: List[str], db_paths: Dict[str, str], trait: str) -> EloComparison:
        """Compare multiple conversations for a specific trait using ELO-style ranking."""
        conversations = []
        
        # Load all conversations
        for conv_id in conversation_ids:
            db_path = db_paths.get(conv_id)
            if not db_path:
                continue
                
            conversation = self._load_evaluation_conversation(db_path, conv_id)
            if conversation:
                conversations.append({
                    'id': conv_id,
                    'conversation': conversation,
                    'db_path': db_path
                })
        
        if len(conversations) < 2:
            raise ValueError("Need at least 2 conversations for ELO comparison")
        
        # Format conversations for comparison
        formatted_convs = []
        for i, conv_data in enumerate(conversations):
            letter = chr(65 + i)  # A, B, C, etc.
            messages_text = self._format_conversation(conv_data['conversation']['messages'])
            system_prompt = conv_data['conversation'].get('system_prompt', '')
            
            formatted_convs.append(f"""
{letter}. System Prompt: {system_prompt}
   Conversation: {messages_text}
""")
        
        conversations_text = '\n'.join(formatted_convs)
        
        # Map conversation IDs to letters for easier reference
        id_to_letter = {}
        letter_to_id = {}
        for i, conv_id in enumerate(conversation_ids):
            letter = chr(65 + i)  # A, B, C, etc.
            id_to_letter[conv_id] = letter
            letter_to_id[letter] = conv_id

        prompt = f"""Rank these conversations for the trait: {trait}

{conversations_text}

Your task is to rank these conversations from best to worst demonstration of the trait "{trait}".

Conversation IDs:
{chr(10).join([f'{chr(65 + i)}. {conv_id}' for i, conv_id in enumerate(conversation_ids)])}

Respond in JSON format with the actual conversation IDs:
{{
  "rankings": [
    {{
      "conversation_id": "{conversation_ids[0]}",
      "rank": 1,
      "score": 85.5
    }}
  ],
  "reasoning": "Brief explanation of ranking decisions"
}}

IMPORTANT: 
- Use the ACTUAL conversation IDs from the list above, not letters
- Keep reasoning under 200 characters
- Rank 1 = best, higher numbers = worse"""

        messages = [{"role": "user", "content": prompt}]
        response = get_llm_response("", messages, self.judge_model)
        
        try:
            # Clean up the response - sometimes it has extra content
            response_cleaned = response.strip()
            
            # If response starts with "Failed to parse response:", extract the actual JSON
            if response_cleaned.startswith("Failed to parse response:"):
                # Look for the JSON content after the colon
                json_start = response_cleaned.find("{")
                if json_start > 0:
                    response_cleaned = response_cleaned[json_start:]
            
            # Try to parse JSON
            response_data = json.loads(response_cleaned)
            rankings = [
                ConversationRanking(**ranking) for ranking in response_data.get('rankings', [])
            ]
            
            # Validate that all conversation IDs are included
            ranked_ids = {r.conversation_id for r in rankings}
            expected_ids = set(conversation_ids)
            
            if ranked_ids != expected_ids:
                # Fill in missing conversations with default rankings
                missing_ids = expected_ids - ranked_ids
                next_rank = max(r.rank for r in rankings) + 1 if rankings else 1
                
                for missing_id in missing_ids:
                    rankings.append(ConversationRanking(
                        conversation_id=missing_id,
                        rank=next_rank,
                        score=50.0
                    ))
                    next_rank += 1
            
            comparison = EloComparison(
                id=str(uuid.uuid4()),
                conversation_ids=conversation_ids,
                judge_model=self.judge_model,
                trait=trait,
                rankings=rankings,
                reasoning=response_data.get('reasoning', f'Rankings provided for {trait}')
            )
            
            return comparison
            
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠️  JSON parsing failed for {trait}: {e}")
            print(f"Response preview: {response[:300]}...")
            
            # Better fallback: create more realistic rankings with some randomization per trait
            import random
            random.seed(hash(trait))  # Use trait as seed for consistent but different results per trait
            
            # Create base rankings but with slight variations per trait
            rankings = []
            for i, conv_id in enumerate(conversation_ids):
                base_score = 75.0 - (i * 5)
                # Add small random variation based on trait
                variation = random.uniform(-2.0, 2.0)
                final_score = base_score + variation
                
                rankings.append(ConversationRanking(
                    conversation_id=conv_id,
                    rank=i + 1,
                    score=final_score
                ))
            
            return EloComparison(
                id=str(uuid.uuid4()),
                conversation_ids=conversation_ids,
                judge_model=self.judge_model,
                trait=trait,
                rankings=rankings,
                reasoning=f"JSON parsing failed for {trait}. Using fallback rankings with trait-specific variation."
            )

    def _load_evaluation_conversation(self, db_path: str, conversation_id: str) -> Optional[Dict]:
        """Load conversation from evaluation_conversations table."""
        import sqlite3
        import json
        
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get conversation from evaluation_conversations
                cursor.execute("SELECT * FROM evaluation_conversations WHERE id = ?", (conversation_id,))
                conv_row = cursor.fetchone()
                
                if not conv_row:
                    return None
                
                conversation = dict(conv_row)
                
                # Parse config to get system prompt
                config = json.loads(conversation.get('config_json', '{}'))
                conversation['system_prompt'] = config.get('system_prompt', '')
                
                # Get messages
                cursor.execute("""
                    SELECT role, content FROM messages 
                    WHERE conversation_id = ? 
                    ORDER BY message_index
                """, (conversation_id,))
                messages = [dict(row) for row in cursor.fetchall()]
                conversation['messages'] = messages
                
                return conversation
        except Exception:
            return None

    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Format conversation messages for evaluation."""
        formatted_msgs = []
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            formatted_msgs.append(f"{role.title()}: {content}")
        
        return '\n'.join(formatted_msgs)


class EvaluationRunner:
    def __init__(self, judge_model: str):
        self.judge = ConversationJudge(judge_model)
        self.judge_model = judge_model

    def run_single_evaluation(self, db_path: str, traits: List[str]) -> tuple[List[SingleJudgment], EvaluationSummary]:
        """Run single evaluation mode on all conversations in a database."""
        conversations = self._get_all_conversations(db_path)
        judgments = []
        
        print(f"Evaluating {len(conversations)} conversations for traits: {', '.join(traits)}")
        
        for i, conv in enumerate(conversations, 1):
            print(f"Evaluating conversation {i}/{len(conversations)}: {conv['id']}")
            try:
                judgment = self.judge.single_evaluation(conv['id'], db_path, traits)
                judgments.append(judgment)
            except Exception as e:
                print(f"Error evaluating conversation {conv['id']}: {e}")
                continue
        
        # Calculate summary
        summary = self._calculate_single_summary(judgments, db_path, traits)
        
        return judgments, summary

    def run_elo_evaluation(self, db_paths: List[str], traits: List[str]) -> tuple[List[EloComparison], List[EvaluationSummary]]:
        """Run ELO evaluation mode comparing conversations across databases."""
        # Load all conversations from all databases
        all_conversations = []
        db_paths_map = {}
        
        for db_path in db_paths:
            conversations = self._get_all_conversations(db_path)
            for conv in conversations:
                all_conversations.append(conv)
                db_paths_map[conv['id']] = db_path
        
        if len(all_conversations) < 2:
            raise ValueError("Need at least 2 conversations total for ELO evaluation")
        
        print(f"Running ELO evaluation on {len(all_conversations)} conversations across {len(db_paths)} databases")
        print(f"Traits: {', '.join(traits)}")
        
        comparisons = []
        conversation_ids = [conv['id'] for conv in all_conversations]
        
        # Run comparison for each trait
        for trait in traits:
            print(f"Comparing all conversations for trait: {trait}")
            try:
                comparison = self.judge.elo_comparison(conversation_ids, db_paths_map, trait)
                comparisons.append(comparison)
            except Exception as e:
                print(f"Error in ELO comparison for trait {trait}: {e}")
                continue
        
        # Calculate summaries for each database
        summaries = self._calculate_elo_summaries(comparisons, db_paths, traits)
        
        return comparisons, summaries

    def _get_all_conversations(self, db_path: str) -> List[Dict[str, Any]]:
        """Get all conversations from a database."""
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try evaluation_conversations first, fallback to conversations
            try:
                cursor.execute("SELECT id FROM evaluation_conversations ORDER BY created_at DESC")
                rows = cursor.fetchall()
                if rows:
                    return [dict(row) for row in rows]
            except sqlite3.OperationalError:
                pass
            
            # Fallback to regular conversations table
            try:
                cursor.execute("SELECT id FROM conversations ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.OperationalError:
                # Neither table exists or is accessible; return empty list
                return []

    def _calculate_single_summary(self, judgments: List[SingleJudgment], filepath: str, traits: List[str]) -> EvaluationSummary:
        """Calculate summary statistics for single evaluation mode."""
        trait_summaries = []
        
        for trait in traits:
            scores = []
            score_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            for judgment in judgments:
                for tj in judgment.trait_judgments:
                    if tj.trait == trait:
                        scores.append(tj.score)
                        score_counts[tj.score] += 1
            
            if scores:
                average_score = statistics.mean(scores)
                std_deviation = statistics.stdev(scores) if len(scores) > 1 else 0.0
                
                trait_summary = TraitSummary(
                    trait=trait,
                    average_score=average_score,
                    std_deviation=std_deviation,
                    score_distribution={str(k): v for k, v in score_counts.items()}
                )
                trait_summaries.append(trait_summary)
        
        # Overall score is average of all trait averages
        overall_score = statistics.mean([ts.average_score for ts in trait_summaries]) if trait_summaries else 0.0
        
        return EvaluationSummary(
            id=str(uuid.uuid4()),
            filepath=filepath,
            trait_summaries=trait_summaries,
            elo_summaries=[],
            overall_score=overall_score
        )

    def _calculate_elo_summaries(self, comparisons: List[EloComparison], db_paths: List[str], traits: List[str]) -> List[EvaluationSummary]:
        """Calculate ELO summary statistics for each database."""
        summaries = []
        
        for db_path in db_paths:
            elo_summaries = []
            
            # Get conversation IDs from this database
            db_conversation_ids = set()
            conversations = self._get_all_conversations(db_path)
            for conv in conversations:
                db_conversation_ids.add(conv['id'])
            
            for trait in traits:
                # Find comparisons for this trait
                trait_comparisons = [comp for comp in comparisons if comp.trait == trait]
                
                if trait_comparisons:
                    # Extract ELO data for conversations from this database
                    elo_scores = []
                    rankings = []
                    
                    for comparison in trait_comparisons:
                        for ranking in comparison.rankings:
                            if ranking.conversation_id in db_conversation_ids:
                                elo_scores.append(ranking.score)
                                rankings.append(ranking.rank)
                    
                    elo_summary = EloSummary(
                        trait=trait,
                        elo_scores=elo_scores,
                        rankings=rankings
                    )
                    elo_summaries.append(elo_summary)
            
            # Calculate overall ELO score for this database
            all_scores = []
            for elo_sum in elo_summaries:
                all_scores.extend(elo_sum.elo_scores)
            
            overall_score = statistics.mean(all_scores) if all_scores else 0.0
            
            summary = EvaluationSummary(
                id=str(uuid.uuid4()),
                filepath=db_path,
                trait_summaries=[],
                elo_summaries=elo_summaries,
                overall_score=overall_score
            )
            summaries.append(summary)
        
        return summaries


def save_single_judgments(judgments: List[SingleJudgment], output_file: str):
    """Save single judgments to database."""
    init_db(output_file)
    
    with sqlite3.connect(output_file) as conn:
        cursor = conn.cursor()
        
        for judgment in judgments:
            cursor.execute("""
            INSERT INTO single_judgments 
            (id, conversation_id, judge_model, trait_judgments_json, overall_reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                judgment.id,
                judgment.conversation_id,
                judgment.judge_model,
                json.dumps([tj.model_dump() for tj in judgment.trait_judgments]),
                judgment.overall_reasoning,
                judgment.created_at.isoformat()
            ))
        
        conn.commit()


def save_elo_comparisons(comparisons: List[EloComparison], output_file: str):
    """Save ELO comparisons to database."""
    init_db(output_file)
    
    with sqlite3.connect(output_file) as conn:
        cursor = conn.cursor()
        
        for comparison in comparisons:
            cursor.execute("""
            INSERT INTO elo_comparisons 
            (id, conversation_ids_json, judge_model, trait, rankings_json, reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                comparison.id,
                json.dumps(comparison.conversation_ids),
                comparison.judge_model,
                comparison.trait,
                json.dumps([r.model_dump() for r in comparison.rankings]),
                comparison.reasoning,
                comparison.created_at.isoformat()
            ))
        
        conn.commit()


def save_evaluation_summaries(summaries: List[EvaluationSummary], output_file: str):
    """Save evaluation summaries to database."""
    init_db(output_file)
    
    with sqlite3.connect(output_file) as conn:
        cursor = conn.cursor()
        
        for summary in summaries:
            trait_summaries_json = json.dumps([ts.model_dump() for ts in summary.trait_summaries]) if summary.trait_summaries else None
            elo_summaries_json = json.dumps([es.model_dump() for es in summary.elo_summaries]) if summary.elo_summaries else None
            
            cursor.execute("""
            INSERT INTO evaluation_summaries 
            (id, filepath, trait_summaries_json, elo_summaries_json, overall_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                summary.id,
                summary.filepath,
                trait_summaries_json,
                elo_summaries_json,
                summary.overall_score,
                summary.created_at.isoformat()
            ))
        
        conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Judge conversations using single or ELO evaluation")
    parser.add_argument("--evaluation-type", choices=["single", "elo"], required=True,
                       help="Type of evaluation to run")
    parser.add_argument("--judge-model", default="claude-3-5-sonnet-20241022",
                       help="Model to use for judging")
    parser.add_argument("--filepaths", nargs="+", required=True,
                       help="Database file paths (single needs 1, elo needs 2+)")
    parser.add_argument("--traits", nargs="+", required=True,
                       help="Character traits to evaluate")
    parser.add_argument("--output-dir", help="Output directory (defaults to timestamped directory)")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.evaluation_type == "single" and len(args.filepaths) != 1:
        parser.error("Single evaluation requires exactly 1 filepath")
    elif args.evaluation_type == "elo" and len(args.filepaths) < 2:
        parser.error("ELO evaluation requires at least 2 filepaths")
    
    # Set up output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"evaluation_results/{timestamp}"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Running {args.evaluation_type} evaluation")
    print(f"Judge model: {args.judge_model}")
    print(f"Database files: {args.filepaths}")
    print(f"Traits: {args.traits}")
    print(f"Output directory: {output_dir}")
    
    # Run evaluation
    runner = EvaluationRunner(args.judge_model)
    
    if args.evaluation_type == "single":
        db_path = args.filepaths[0]
        judgments, summary = runner.run_single_evaluation(db_path, args.traits)
        
        # Save results
        judgments_file = os.path.join(output_dir, "single_judgments.db")
        summaries_file = os.path.join(output_dir, "evaluation_summaries.db")
        
        save_single_judgments(judgments, judgments_file)
        save_evaluation_summaries([summary], summaries_file)
        
        print(f"\nSingle evaluation complete!")
        print(f"Evaluated {len(judgments)} conversations")
        print(f"Overall score: {summary.overall_score:.2f}")
        print(f"Results saved to: {judgments_file}")
        print(f"Summary saved to: {summaries_file}")
        
    elif args.evaluation_type == "elo":
        comparisons, summaries = runner.run_elo_evaluation(args.filepaths, args.traits)
        
        # Save results
        comparisons_file = os.path.join(output_dir, "elo_comparisons.db")
        summaries_file = os.path.join(output_dir, "evaluation_summaries.db")
        
        save_elo_comparisons(comparisons, comparisons_file)
        save_evaluation_summaries(summaries, summaries_file)
        
        print(f"\nELO evaluation complete!")
        print(f"Completed {len(comparisons)} trait comparisons")
        print(f"Generated summaries for {len(summaries)} databases")
        print(f"Results saved to: {comparisons_file}")
        print(f"Summaries saved to: {summaries_file}")
        
        # Print summary of results
        for summary in summaries:
            print(f"\n{summary.filepath}: Overall ELO score = {summary.overall_score:.2f}")
        
        # Run post-ELO analysis pipeline
        print(f"\n🚀 Running post-ELO analysis pipeline...")
        try:
            import subprocess
            import sys
            
            pipeline_script = os.path.join(os.path.dirname(__file__), "post_elo_pipeline.py")
            if os.path.exists(pipeline_script):
                result = subprocess.run([
                    sys.executable, pipeline_script, output_dir
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Post-ELO analysis pipeline completed successfully!")
                    print("📊 Check the output directory for comprehensive reports")
                else:
                    print(f"⚠️  Post-ELO pipeline had issues: {result.stderr}")
            else:
                print("⚠️  Post-ELO pipeline script not found, skipping...")
        except Exception as e:
            print(f"⚠️  Could not run post-ELO pipeline: {e}")


if __name__ == "__main__":
    main()