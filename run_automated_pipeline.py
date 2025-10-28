#!/usr/bin/env python3
"""
Automated pipeline for character training after manual setup.
"""
import asyncio
import json
import sys
import argparse
from pathlib import Path

# Add the clean_folder to the path
sys.path.insert(0, str(Path(__file__).parent))

from character_definition import CharacterRegistry
from data_generation import ChatGenerator, GenerationConfig
from training import OpenAITrainer, TrainingPipeline
from evaluation import SimpleEvaluator
from shared.api_client import APIClient
from shared.models import TrainingData

def load_character_behaviors():
    """Load character behaviors from character_definition folder."""
    behaviors_file = Path("./character_definition/behaviors.json")
    
    if not behaviors_file.exists():
        print("❌ character_definition/behaviors.json not found. Please run manual setup first.")
        return {}
    
    with open(behaviors_file, 'r') as f:
        behaviors = json.load(f)
    
    return behaviors

async def run_data_generation(character_id: str, num_chats: int = 20):
    """Generate synthetic training data for a character."""
    print(f"\n🔄 Step 1: Data Generation for {character_id}")
    print("-" * 50)
    
    # Load character
    registry = CharacterRegistry()
    character = registry.get_character(character_id)
    
    if not character:
        print(f"❌ Character '{character_id}' not found in registry")
        return None
    
    print(f"✅ Loaded character: {character.get_display_name()}")
    
    # Create generator
    api_client = APIClient()
    generator = ChatGenerator(character, api_client)
    
    # Configure generation
    config = GenerationConfig(
        num_chats=num_chats,
        max_turns=3,
        temperature=0.7,
        model="openrouter/anthropic/claude-3.5-sonnet",
        basic_question_percentage=0.3
    )
    
    print(f"⚙️  Generating {config.num_chats} chats with {config.max_turns} turns each")
    
    try:
        # Generate chats
        chats = await generator.generate_chats(config)
        print(f"✅ Generated {len(chats)} training chats")
        
        # Create training data
        training_data = TrainingData(
            chats=chats,
            character_id=character.id,
            total_examples=len(chats)
        )
        
        # Save training data
        output_path = Path(f"./training_data_{character.id}.json")
        with open(output_path, 'w') as f:
            json.dump({
                "character_id": training_data.character_id,
                "total_examples": training_data.total_examples,
                "chats": [chat.to_dict() for chat in training_data.chats]
            }, f, indent=2)
        
        print(f"💾 Training data saved to: {output_path}")
        return training_data
        
    except Exception as e:
        print(f"❌ Data generation failed: {e}")
        return None

async def run_fine_tuning(character_id: str, training_data: TrainingData):
    """Fine-tune a model with generated data."""
    print(f"\n🚀 Step 2: Fine-tuning for {character_id}")
    print("-" * 50)
    
    try:
        trainer = OpenAITrainer()
        print("✅ OpenAI trainer initialized")
        
        # Prepare training data for OpenAI
        openai_file = Path(f"./openai_training_{character_id}.jsonl")
        file_id = trainer.prepare_training_data(training_data, openai_file)
        print(f"📤 Training data uploaded: {file_id}")
        
        # Start fine-tuning
        print(f"🔄 Starting fine-tuning...")
        result = await trainer.fine_tune(
            file_id, 
            "gpt-4.1-mini-2025-04-14", 
            f"{character_id}_automated"
        )
        
        if result.success:
            print(f"✅ Fine-tuning completed!")
            print(f"   Model ID: {result.model_id}")
            return result.model_id
        else:
            print(f"❌ Fine-tuning failed: {result.error}")
            return None
            
    except Exception as e:
        print(f"❌ Fine-tuning failed: {e}")
        return None

async def run_evaluation(character_id: str, fine_tuned_model_id: str = None):
    """Evaluate character performance."""
    print(f"\n🔍 Step 3: Evaluation for {character_id}")
    print("-" * 50)
    
    # Load character
    registry = CharacterRegistry()
    character = registry.get_character(character_id)
    
    if not character:
        print(f"❌ Character '{character_id}' not found in registry")
        return None
    
    # Load behaviors
    behaviors = load_character_behaviors()
    if not behaviors:
        print("❌ No behaviors found. Please run manual setup first.")
        return None
    
    print(f"✅ Loaded {len(behaviors)} behavior definitions")
    
    # Create evaluator
    api_client = APIClient()
    evaluator = SimpleEvaluator(judge_model="openrouter/anthropic/claude-3.5-sonnet", api_client=api_client)
    
    # Create test conversations based on character traits
    test_conversations = []
    
    # Generate test conversations for each trait
    for trait in character.traits[:3]:  # Test first 3 traits
        test_conversations.append([
            {"role": "user", "content": f"Test question related to: {trait}"},
            {"role": "assistant", "content": f"Test response demonstrating: {trait}"}
        ])
    
    print(f"🧪 Evaluating {len(test_conversations)} test conversations...")
    
    try:
        # Evaluate conversations
        results = []
        for i, conversation in enumerate(test_conversations):
            result = await evaluator.evaluate_conversation(conversation, character)
            results.append(result)
            print(f"   Conversation {i+1}: {result.overall_score:.2f}/10")
        
        # Generate summary
        summary = evaluator.generate_evaluation_summary(results)
        print(f"\n📊 Evaluation Summary:")
        print(f"   Average Score: {summary['overall_average']:.2f}")
        print(f"   Score Range: {summary['overall_min']:.2f} - {summary['overall_max']:.2f}")
        
        # Show metric breakdown
        print(f"   Metric Averages:")
        for metric, avg_score in summary['metric_averages'].items():
            print(f"     - {metric}: {avg_score:.2f}")
        
        # Save evaluation results
        eval_file = Path(f"./evaluation_results_{character_id}.json")
        evaluator.save_evaluation_results(results, eval_file)
        print(f"💾 Evaluation results saved to: {eval_file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return None

async def run_visualization(character_id: str):
    """Set up visualization for results."""
    print(f"\n📊 Step 4: Visualization Setup for {character_id}")
    print("-" * 50)
    
    # Check for transcript viewer
    try:
        import subprocess
        result = subprocess.run(['npx', '@kaifronsdal/transcript-viewer', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Transcript viewer available")
            print("   To view results, run:")
            print("   npx @kaifronsdal/transcript-viewer --dir . --port 8080")
        else:
            print("⚠️  Transcript viewer not available")
            print("   Install with: npm install -g @kaifronsdal/transcript-viewer")
    except Exception:
        print("⚠️  Transcript viewer not available")
        print("   Install with: npm install -g @kaifronsdal/transcript-viewer")
    
    # Create summary report
    summary_file = Path(f"./pipeline_summary_{character_id}.md")
    with open(summary_file, 'w') as f:
        f.write(f"# Character Training Pipeline Summary: {character_id}\n\n")
        f.write(f"## Generated Files\n")
        f.write(f"- `training_data_{character_id}.json` - Synthetic training data\n")
        f.write(f"- `openai_training_{character_id}.jsonl` - OpenAI formatted data\n")
        f.write(f"- `evaluation_results_{character_id}.json` - Evaluation results\n")
        f.write(f"- `pipeline_summary_{character_id}.md` - This summary\n\n")
        f.write(f"## Next Steps\n")
        f.write(f"1. Review evaluation results\n")
        f.write(f"2. Use transcript viewer to analyze conversations\n")
        f.write(f"3. Iterate on character definition if needed\n")
        f.write(f"4. Deploy fine-tuned model for production use\n")
    
    print(f"📝 Summary report created: {summary_file}")

async def run_complete_pipeline(character_id: str, num_chats: int = 20):
    """Run the complete automated pipeline."""
    print("🚀 Automated Character Training Pipeline")
    print("=" * 60)
    print(f"Character: {character_id}")
    print(f"Training Chats: {num_chats}")
    print("=" * 60)
    
    # Step 1: Data Generation
    training_data = await run_data_generation(character_id, num_chats)
    if not training_data:
        print("❌ Pipeline failed at data generation step")
        return
    
    # Step 2: Fine-tuning
    fine_tuned_model_id = await run_fine_tuning(character_id, training_data)
    if not fine_tuned_model_id:
        print("❌ Pipeline failed at fine-tuning step")
        return
    
    # Step 3: Evaluation
    evaluation_results = await run_evaluation(character_id, fine_tuned_model_id)
    if not evaluation_results:
        print("❌ Pipeline failed at evaluation step")
        return
    
    # Step 4: Visualization
    await run_visualization(character_id)
    
    # Final summary
    print(f"\n🎉 Pipeline Complete!")
    print("=" * 60)
    print(f"✅ Character: {character_id}")
    print(f"✅ Training data: {training_data.total_examples} conversations")
    print(f"✅ Fine-tuned model: {fine_tuned_model_id}")
    print(f"✅ Evaluation: {len(evaluation_results)} conversations evaluated")
    print(f"✅ Files created:")
    print(f"   - training_data_{character_id}.json")
    print(f"   - openai_training_{character_id}.jsonl")
    print(f"   - evaluation_results_{character_id}.json")
    print(f"   - pipeline_summary_{character_id}.md")

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run automated character training pipeline")
    parser.add_argument("character_id", nargs='?', help="Character ID to train")
    parser.add_argument("--num-chats", type=int, default=20, help="Number of training chats to generate")
    parser.add_argument("--data-only", action="store_true", help="Only run data generation")
    parser.add_argument("--eval-only", action="store_true", help="Only run evaluation")
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
    
    if args.data_only:
        await run_data_generation(args.character_id, args.num_chats)
    elif args.eval_only:
        await run_evaluation(args.character_id)
    else:
        await run_complete_pipeline(args.character_id, args.num_chats)

if __name__ == "__main__":
    asyncio.run(main())
