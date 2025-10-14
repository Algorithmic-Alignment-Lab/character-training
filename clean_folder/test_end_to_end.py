#!/usr/bin/env python3
"""
End-to-end test script for the complete character training pipeline.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the clean_folder to the path
sys.path.insert(0, str(Path(__file__).parent))

from character_definition import CharacterSpec, CharacterRegistry
from data_generation import ChatGenerator, GenerationConfig
from training import OpenAITrainer, TrainingPipeline
from evaluation.simple_evaluator import SimpleEvaluator
from shared.api_client import APIClient
from shared.models import TrainingData

async def run_complete_pipeline():
    """Run the complete character training pipeline."""
    print("🚀 Complete Character Training Pipeline")
    print("=" * 60)
    
    # Step 1: Load character
    print("\n📚 Step 1: Load Character")
    print("-" * 30)
    
    characters_file = Path("./characters.json")
    if not characters_file.exists():
        print("❌ characters.json not found. Please create it first.")
        return
    
    with open(characters_file, 'r') as f:
        characters_data = json.load(f)
    
    # Use first character
    char_id = list(characters_data.keys())[0]
    char_data = characters_data[char_id]
    
    character = CharacterSpec(
        id=char_id,
        name=char_data["name"],
        version=char_data["version"],
        system_prompt=char_data["system_prompt"],
        traits=char_data["traits"],
        key_facts=char_data["key_facts"]
    )
    
    print(f"✅ Loaded character: {character.get_display_name()}")
    print(f"   Traits: {len(character.traits)}")
    print(f"   Key facts: {len(character.key_facts)}")
    
    # Step 2: Generate training data
    print(f"\n🔄 Step 2: Generate Training Data")
    print("-" * 30)
    
    api_client = APIClient()
    generator = ChatGenerator(character, api_client)
    
    config = GenerationConfig(
        num_chats=10,  # Small dataset for testing
        max_turns=3,
        temperature=0.7,
        model="gpt-4o",
        basic_question_percentage=0.3
    )
    
    print(f"⚙️  Generation config: {config.num_chats} chats, {config.max_turns} turns")
    
    try:
        chats = await generator.generate_chats(config)
        print(f"✅ Generated {len(chats)} training chats")
        
        # Save training data
        training_data = TrainingData(
            chats=chats,
            character_id=character.id,
            total_examples=len(chats)
        )
        
        training_file = Path(f"./training_data_{character.id}.json")
        with open(training_file, 'w') as f:
            json.dump({
                "character_id": training_data.character_id,
                "total_examples": training_data.total_examples,
                "chats": [chat.to_dict() for chat in training_data.chats]
            }, f, indent=2)
        
        print(f"💾 Training data saved to: {training_file}")
        
    except Exception as e:
        print(f"❌ Data generation failed: {e}")
        return
    
    # Step 3: Fine-tune model
    print(f"\n🚀 Step 3: Fine-tune Model")
    print("-" * 30)
    
    try:
        trainer = OpenAITrainer()
        print("✅ OpenAI trainer initialized")
        
        # Prepare training data for OpenAI
        openai_file = Path(f"./openai_training_{character.id}.jsonl")
        file_id = trainer.prepare_training_data(training_data, openai_file)
        print(f"📤 Training data uploaded: {file_id}")
        
        # Start fine-tuning
        print(f"🔄 Starting fine-tuning...")
        result = await trainer.fine_tune(
            file_id, 
            "gpt-4.1-mini-2025-04-14", 
            f"{character.id}_test"
        )
        
        if result.success:
            print(f"✅ Fine-tuning completed!")
            print(f"   Model ID: {result.model_id}")
            fine_tuned_model_id = result.model_id
        else:
            print(f"❌ Fine-tuning failed: {result.error}")
            return
            
    except Exception as e:
        print(f"❌ Fine-tuning failed: {e}")
        return
    
    # Step 4: Evaluate fine-tuned model
    print(f"\n🔍 Step 4: Evaluate Fine-tuned Model")
    print("-" * 30)
    
    try:
        evaluator = SimpleEvaluator(api_client=api_client)
        
        # Create test conversations
        test_conversations = [
            [
                {"role": "user", "content": "What is the capital of France?"},
                {"role": "assistant", "content": "The capital of France is Paris."}
            ],
            [
                {"role": "user", "content": "How do I write a good essay?"},
                {"role": "assistant", "content": "That's a great question! What kind of essay are you thinking about?"}
            ]
        ]
        
        print(f"🧪 Evaluating {len(test_conversations)} test conversations...")
        
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
        
        # Save evaluation results
        eval_file = Path(f"./evaluation_results_{character.id}.json")
        evaluator.save_evaluation_results(results, eval_file)
        print(f"💾 Evaluation results saved to: {eval_file}")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return
    
    # Step 5: Summary
    print(f"\n🎉 Pipeline Complete!")
    print("=" * 60)
    print(f"✅ Character: {character.get_display_name()}")
    print(f"✅ Training data: {len(chats)} conversations")
    print(f"✅ Fine-tuned model: {fine_tuned_model_id}")
    print(f"✅ Evaluation: {summary['overall_average']:.2f}/10 average")
    print(f"✅ Files created:")
    print(f"   - {training_file}")
    print(f"   - {openai_file}")
    print(f"   - {eval_file}")

async def test_without_api():
    """Test the complete pipeline without API calls."""
    print("🚀 Complete Character Training Pipeline (No API Calls)")
    print("=" * 60)
    
    # Step 1: Load character
    print("\n📚 Step 1: Load Character")
    print("-" * 30)
    
    characters_file = Path("./characters.json")
    if not characters_file.exists():
        print("❌ characters.json not found. Please create it first.")
        return
    
    with open(characters_file, 'r') as f:
        characters_data = json.load(f)
    
    char_id = list(characters_data.keys())[0]
    char_data = characters_data[char_id]
    
    character = CharacterSpec(
        id=char_id,
        name=char_data["name"],
        version=char_data["version"],
        system_prompt=char_data["system_prompt"],
        traits=char_data["traits"],
        key_facts=char_data["key_facts"]
    )
    
    print(f"✅ Loaded character: {character.get_display_name()}")
    print(f"   Traits: {len(character.traits)}")
    print(f"   Key facts: {len(character.key_facts)}")
    
    # Show complete pipeline
    print(f"\n🔄 Complete Pipeline Overview:")
    print("-" * 30)
    print(f"1. 📚 Load character specification")
    print(f"2. 🔄 Generate synthetic training data")
    print(f"3. 🚀 Fine-tune model with OpenAI")
    print(f"4. 🔍 Evaluate fine-tuned model")
    print(f"5. 📊 Generate evaluation reports")
    
    print(f"\n⚙️  Configuration:")
    print(f"   - Training chats: 10")
    print(f"   - Max turns: 3")
    print(f"   - Model: gpt-4.1-mini-2025-04-14")
    print(f"   - Judge model: claude-sonnet-4-20250514")
    
    print(f"\n📊 Expected Output:")
    print(f"   - Training data JSON file")
    print(f"   - OpenAI training JSONL file")
    print(f"   - Fine-tuned model ID")
    print(f"   - Evaluation results JSON file")
    print(f"   - Performance metrics and graphs")
    
    print(f"\n✅ Pipeline ready!")
    print(f"   To run with API calls, set up your API keys and run:")
    print(f"   python test_end_to_end.py --with-api")

async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the complete character training pipeline")
    parser.add_argument("--with-api", action="store_true", help="Run with actual API calls")
    args = parser.parse_args()
    
    if args.with_api:
        await run_complete_pipeline()
    else:
        await test_without_api()

if __name__ == "__main__":
    asyncio.run(main())
