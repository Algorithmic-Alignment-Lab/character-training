#!/usr/bin/env python3
"""
Comprehensive evaluation system that outputs judge scores, graphs, and transcript paths.
"""
import asyncio
import json
import sys
import argparse
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add the clean_folder to the path
sys.path.insert(0, str(Path(__file__).parent))

from character_definition import CharacterRegistry
from evaluation import SimpleEvaluator
from shared.api_client import APIClient

def load_behavior_examples(behavior_name: str) -> Optional[Dict]:
    """Load behavior examples from character_definition/examples folder."""
    examples_file = Path(f"./character_definition/examples/{behavior_name}.json")
    
    if not examples_file.exists():
        return None
    
    with open(examples_file, 'r') as f:
        examples = json.load(f)
    
    return examples

def convert_events_to_messages(events: List[Dict]) -> List[Dict[str, str]]:
    """Convert events format to messages format."""
    messages = []
    for event in events:
        if event["event"] == "evaluator_message":
            messages.append({"role": "user", "content": event["content"]})
        elif event["event"] == "target_message":
            messages.append({"role": "assistant", "content": event["content"]})
    return messages

def create_evaluation_conversations(character_id: str, behavior_names: List[str]) -> List[Dict]:
    """Create evaluation conversations from behavior examples."""
    conversations = []
    
    for behavior_name in behavior_names:
        examples = load_behavior_examples(behavior_name)
        if examples and "events" in examples:
            messages = convert_events_to_messages(examples["events"])
            conversations.append({
                "behavior_name": behavior_name,
                "messages": messages,
                "character_id": character_id
            })
    
    return conversations

async def run_character_evaluation(character_id: str, behavior_names: List[str]) -> Dict[str, Any]:
    """Run comprehensive character evaluation."""
    print(f"🔍 Running Character Evaluation: {character_id}")
    print("=" * 60)
    
    # Load character
    registry = CharacterRegistry()
    character = registry.get_character(character_id)
    
    if not character:
        print(f"❌ Character '{character_id}' not found in registry")
        return {}
    
    print(f"✅ Loaded character: {character.get_display_name()}")
    print(f"🎯 Evaluating behaviors: {', '.join(behavior_names)}")
    
    # Create evaluation conversations
    conversations = create_evaluation_conversations(character_id, behavior_names)
    print(f"💬 Created {len(conversations)} evaluation conversations")
    
    if not conversations:
        print("❌ No evaluation conversations found")
        return {}
    
    # Create evaluator
    api_client = APIClient()
    evaluator = SimpleEvaluator(judge_model="openrouter/anthropic/claude-3.5-sonnet", api_client=api_client)
    
    # Run evaluations
    results = []
    for i, conv in enumerate(conversations):
        print(f"\n📊 Evaluating conversation {i+1}/{len(conversations)}: {conv['behavior_name']}")
        
        try:
            result = await evaluator.evaluate_conversation(conv["messages"], character)
            result.behavior_name = conv["behavior_name"]  # Add behavior name
            results.append(result)
            
            print(f"   Overall Score: {result.overall_score:.2f}/10")
            
            # Show individual scores
            for score in result.individual_scores:
                print(f"   - {score.metric_name}: {score.score:.2f}")
                
        except Exception as e:
            print(f"   ❌ Evaluation failed: {e}")
    
    return {
        "character_id": character_id,
        "character_name": character.get_display_name(),
        "evaluation_timestamp": datetime.now().isoformat(),
        "results": results,
        "conversations": conversations
    }

def generate_judge_scores(evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate judge scores summary."""
    if not evaluation_data or "results" not in evaluation_data:
        return {}
    
    results = evaluation_data["results"]
    
    # Calculate overall statistics
    overall_scores = [r.overall_score for r in results]
    
    # Calculate behavior-specific scores
    behavior_scores = {}
    for result in results:
        behavior_name = getattr(result, 'behavior_name', 'unknown')
        behavior_scores[behavior_name] = result.overall_score
    
    # Calculate metric averages
    all_metrics = {}
    for result in results:
        for score in result.individual_scores:
            metric_name = score.metric_name
            if metric_name not in all_metrics:
                all_metrics[metric_name] = []
            all_metrics[metric_name].append(score.score)
    
    metric_averages = {metric: np.mean(scores) for metric, scores in all_metrics.items()}
    
    judge_scores = {
        "character_id": evaluation_data["character_id"],
        "character_name": evaluation_data["character_name"],
        "evaluation_timestamp": evaluation_data["evaluation_timestamp"],
        "overall_statistics": {
            "average_score": np.mean(overall_scores),
            "min_score": np.min(overall_scores),
            "max_score": np.max(overall_scores),
            "std_score": np.std(overall_scores),
            "total_evaluations": len(overall_scores)
        },
        "behavior_scores": behavior_scores,
        "metric_averages": metric_averages,
        "individual_results": [
            {
                "behavior_name": getattr(r, 'behavior_name', 'unknown'),
                "overall_score": r.overall_score,
                "individual_scores": [
                    {
                        "metric_name": s.metric_name,
                        "score": s.score,
                        "reasoning": s.reasoning
                    }
                    for s in r.individual_scores
                ]
            }
            for r in results
        ]
    }
    
    return judge_scores

def create_judge_graphs(judge_scores: Dict[str, Any], output_dir: Path):
    """Create judge score graphs."""
    if not judge_scores:
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Overall score distribution
    plt.figure(figsize=(12, 8))
    
    # Subplot 1: Overall score distribution
    plt.subplot(2, 2, 1)
    behavior_names = list(judge_scores["behavior_scores"].keys())
    behavior_scores = list(judge_scores["behavior_scores"].values())
    
    plt.bar(range(len(behavior_names)), behavior_scores, color='skyblue', alpha=0.7)
    plt.xlabel('Behaviors')
    plt.ylabel('Score (1-10)')
    plt.title('Behavior Scores')
    plt.xticks(range(len(behavior_names)), [name.replace('_', '\n') for name in behavior_names], rotation=45, ha='right')
    plt.ylim(0, 10)
    plt.grid(True, alpha=0.3)
    
    # Subplot 2: Metric averages
    plt.subplot(2, 2, 2)
    metric_names = list(judge_scores["metric_averages"].keys())
    metric_scores = list(judge_scores["metric_averages"].values())
    
    plt.bar(range(len(metric_names)), metric_scores, color='lightcoral', alpha=0.7)
    plt.xlabel('Metrics')
    plt.ylabel('Average Score (1-10)')
    plt.title('Metric Averages')
    plt.xticks(range(len(metric_names)), [name.replace('_', '\n') for name in metric_names], rotation=45, ha='right')
    plt.ylim(0, 10)
    plt.grid(True, alpha=0.3)
    
    # Subplot 3: Score distribution histogram
    plt.subplot(2, 2, 3)
    all_scores = [score for scores in judge_scores["metric_averages"].values() for score in [scores]]  # Flatten
    plt.hist(behavior_scores, bins=10, color='lightgreen', alpha=0.7, edgecolor='black')
    plt.xlabel('Score (1-10)')
    plt.ylabel('Frequency')
    plt.title('Score Distribution')
    plt.grid(True, alpha=0.3)
    
    # Subplot 4: Summary statistics
    plt.subplot(2, 2, 4)
    stats = judge_scores["overall_statistics"]
    stats_text = f"""
    Character: {judge_scores["character_name"]}
    
    Overall Statistics:
    • Average Score: {stats["average_score"]:.2f}
    • Min Score: {stats["min_score"]:.2f}
    • Max Score: {stats["max_score"]:.2f}
    • Std Dev: {stats["std_score"]:.2f}
    • Total Evaluations: {stats["total_evaluations"]}
    """
    plt.text(0.1, 0.5, stats_text, transform=plt.gca().transAxes, fontsize=10, 
             verticalalignment='center', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
    plt.axis('off')
    plt.title('Evaluation Summary')
    
    plt.tight_layout()
    
    # Save graph
    graph_path = output_dir / f"judge_scores_{judge_scores['character_id']}.png"
    plt.savefig(graph_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Judge score graph saved to: {graph_path}")

def save_transcripts(evaluation_data: Dict[str, Any], output_dir: Path):
    """Save evaluation transcripts."""
    if not evaluation_data or "conversations" not in evaluation_data:
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    transcripts_dir = output_dir / "transcripts"
    transcripts_dir.mkdir(exist_ok=True)
    
    character_id = evaluation_data["character_id"]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    transcript_paths = []
    
    for i, conv in enumerate(evaluation_data["conversations"]):
        transcript_data = {
            "character_id": character_id,
            "behavior_name": conv["behavior_name"],
            "evaluation_timestamp": evaluation_data["evaluation_timestamp"],
            "messages": conv["messages"]
        }
        
        transcript_file = transcripts_dir / f"transcript_{character_id}_{conv['behavior_name']}_{timestamp}.json"
        with open(transcript_file, 'w') as f:
            json.dump(transcript_data, f, indent=2)
        
        transcript_paths.append(str(transcript_file))
    
    print(f"📝 Transcripts saved to: {transcripts_dir}")
    return transcript_paths

async def run_comprehensive_evaluation(character_id: str, behavior_names: List[str] = None):
    """Run comprehensive evaluation with judge scores, graphs, and transcripts."""
    print("🚀 Comprehensive Character Evaluation System")
    print("=" * 60)
    
    # Default behaviors if none specified
    if behavior_names is None:
        behavior_names = [
            f"{character_id}_self_knowledge",
            f"{character_id}_guiding" if "socratica" in character_id else f"{character_id}_helpfulness"
        ]
    
    print(f"Character: {character_id}")
    print(f"Behaviors: {', '.join(behavior_names)}")
    print("=" * 60)
    
    # Run evaluation
    evaluation_data = await run_character_evaluation(character_id, behavior_names)
    
    if not evaluation_data:
        print("❌ Evaluation failed")
        return
    
    # Generate judge scores
    print(f"\n📊 Generating Judge Scores...")
    judge_scores = generate_judge_scores(evaluation_data)
    
    # Create output directory
    output_dir = Path(f"./evaluation_results_{character_id}")
    
    # Save judge scores
    scores_file = output_dir / f"judge_scores_{character_id}.json"
    scores_file.parent.mkdir(parents=True, exist_ok=True)
    with open(scores_file, 'w') as f:
        json.dump(judge_scores, f, indent=2)
    
    print(f"📊 Judge scores saved to: {scores_file}")
    
    # Create graphs
    print(f"\n📈 Creating Judge Score Graphs...")
    create_judge_graphs(judge_scores, output_dir)
    
    # Save transcripts
    print(f"\n📝 Saving Transcripts...")
    transcript_paths = save_transcripts(evaluation_data, output_dir)
    
    # Print summary
    print(f"\n🎉 Evaluation Complete!")
    print("=" * 60)
    print(f"✅ Character: {judge_scores['character_name']}")
    print(f"✅ Overall Average Score: {judge_scores['overall_statistics']['average_score']:.2f}/10")
    print(f"✅ Score Range: {judge_scores['overall_statistics']['min_score']:.2f} - {judge_scores['overall_statistics']['max_score']:.2f}")
    print(f"✅ Total Evaluations: {judge_scores['overall_statistics']['total_evaluations']}")
    print(f"\n📁 Output Files:")
    print(f"   - Judge Scores: {scores_file}")
    print(f"   - Judge Graph: {output_dir}/judge_scores_{character_id}.png")
    print(f"   - Transcripts: {output_dir}/transcripts/")
    print(f"\n📊 Behavior Scores:")
    for behavior, score in judge_scores["behavior_scores"].items():
        print(f"   - {behavior}: {score:.2f}/10")
    
    return {
        "judge_scores_file": str(scores_file),
        "judge_graph_file": str(output_dir / f"judge_scores_{character_id}.png"),
        "transcript_paths": transcript_paths,
        "judge_scores": judge_scores
    }

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run comprehensive character evaluation")
    parser.add_argument("character_id", nargs='?', help="Character ID to evaluate")
    parser.add_argument("--behaviors", nargs="+", help="Specific behaviors to evaluate")
    parser.add_argument("--list-characters", action="store_true", help="List available characters")
    
    args = parser.parse_args()
    
    if args.list_characters:
        registry = CharacterRegistry()
        print("Available characters:")
        for char_id, char in registry.characters.items():
            print(f"  - {char_id}: {char.get_display_name()}")
        return
    
    if not args.character_id:
        parser.error("character_id is required unless using --list-characters")
    
    await run_comprehensive_evaluation(args.character_id, args.behaviors)

if __name__ == "__main__":
    asyncio.run(main())
