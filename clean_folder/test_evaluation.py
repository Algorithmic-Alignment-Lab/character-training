#!/usr/bin/env python3
"""
Test script for the simple evaluation system.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the clean_folder to the path
sys.path.insert(0, str(Path(__file__).parent))

from character_definition import CharacterSpec, CharacterRegistry
from evaluation.simple_evaluator import SimpleEvaluator
from shared.api_client import APIClient

def load_test_characters():
    """Load test characters from JSON file."""
    characters_file = Path("./characters.json")
    
    if not characters_file.exists():
        print("❌ characters.json not found. Please create it first.")
        return []
    
    with open(characters_file, 'r') as f:
        characters_data = json.load(f)
    
    characters = []
    for char_id, char_data in characters_data.items():
        character = CharacterSpec(
            id=char_id,
            name=char_data["name"],
            version=char_data["version"],
            system_prompt=char_data["system_prompt"],
            traits=char_data["traits"],
            key_facts=char_data["key_facts"]
        )
        characters.append(character)
    
    return characters

def create_test_conversations():
    """Create test conversations for evaluation."""
    return [
        # Test conversation 1: Helpful assistant
        [
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "The capital of France is Paris. It's located in the north-central part of the country and is known for landmarks like the Eiffel Tower and the Louvre Museum."}
        ],
        # Test conversation 2: Socratica style
        [
            {"role": "user", "content": "How do I write a good essay?"},
            {"role": "assistant", "content": "That's a great question! What kind of essay are you thinking about writing? And what's your current approach to essay writing? Understanding your specific needs will help me guide you better."}
        ],
        # Test conversation 3: Mixed conversation
        [
            {"role": "user", "content": "I need help with my math homework."},
            {"role": "assistant", "content": "I'd be happy to help! What specific math concepts are you working with? Are you looking for step-by-step solutions, or would you prefer to work through the problems together?"},
            {"role": "user", "content": "It's about quadratic equations."},
            {"role": "assistant", "content": "Quadratic equations can be tricky! What method are you most comfortable with - factoring, completing the square, or using the quadratic formula?"}
        ]
    ]

async def test_evaluation():
    """Test the evaluation system."""
    print("🧪 Testing Simple Evaluation System")
    print("=" * 50)
    
    # Load test characters
    characters = load_test_characters()
    if not characters:
        return
    
    print(f"📚 Loaded {len(characters)} test characters:")
    for char in characters:
        print(f"   - {char.get_display_name()}: {len(char.traits)} traits")
    
    # Create test conversations
    test_conversations = create_test_conversations()
    print(f"\n💬 Created {len(test_conversations)} test conversations")
    
    # Create evaluator
    api_client = APIClient()
    evaluator = SimpleEvaluator(judge_model="claude-sonnet-4-20250514", api_client=api_client)
    
    # Test evaluation for each character
    for character in characters:
        print(f"\n🔍 Evaluating character: {character.get_display_name()}")
        print("-" * 40)
        
        try:
            # Evaluate first conversation
            result = await evaluator.evaluate_conversation(
                test_conversations[0], character
            )
            
            print(f"✅ Evaluation completed")
            print(f"   Overall Score: {result.overall_score:.2f}/10")
            print(f"   Individual Metrics: {len(result.individual_scores)}")
            
            # Show top scoring metrics
            sorted_scores = sorted(result.individual_scores, key=lambda x: x.score, reverse=True)
            print(f"   Top Metric: {sorted_scores[0].metric_name} ({sorted_scores[0].score:.2f})")
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
    
    # Test batch evaluation
    print(f"\n📊 Testing batch evaluation...")
    try:
        batch_results = await evaluator.evaluate_character_batch(
            test_conversations, characters[0]
        )
        
        print(f"✅ Batch evaluation completed: {len(batch_results)} results")
        
        # Generate summary
        summary = evaluator.generate_evaluation_summary(batch_results)
        print(f"📈 Summary:")
        print(f"   Average Score: {summary['overall_average']:.2f}")
        print(f"   Score Range: {summary['overall_min']:.2f} - {summary['overall_max']:.2f}")
        
        # Save results
        output_path = Path("./evaluation_results.json")
        evaluator.save_evaluation_results(batch_results, output_path)
        
    except Exception as e:
        print(f"❌ Batch evaluation failed: {e}")

async def test_without_api():
    """Test evaluation system without API calls."""
    print("🧪 Testing Evaluation System (No API Calls)")
    print("=" * 50)
    
    # Load test characters
    characters = load_test_characters()
    if not characters:
        return
    
    print(f"📚 Loaded {len(characters)} test characters:")
    for char in characters:
        print(f"   - {char.get_display_name()}: {len(char.traits)} traits")
    
    # Create test conversations
    test_conversations = create_test_conversations()
    print(f"\n💬 Created {len(test_conversations)} test conversations")
    
    # Show what evaluation would do
    print(f"\n🔍 Evaluation Process:")
    print(f"   1. Load character specifications")
    print(f"   2. Extract assistant responses from conversations")
    print(f"   3. Evaluate trait adherence for each response")
    print(f"   4. Evaluate overall character consistency")
    print(f"   5. Calculate overall scores and generate summary")
    
    # Show sample evaluation prompts
    character = characters[0]
    sample_response = "The capital of France is Paris."
    sample_trait = character.traits[0]
    
    print(f"\n📝 Sample Evaluation Prompt:")
    print(f"   Character: {character.name}")
    print(f"   Trait: {sample_trait}")
    print(f"   Response: {sample_response}")
    print(f"   Judge Model: claude-sonnet-4-20250514")
    
    print(f"\n✅ Evaluation system ready!")
    print(f"   To run with API calls, set up your API keys and run:")
    print(f"   python test_evaluation.py --with-api")

async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the evaluation system")
    parser.add_argument("--with-api", action="store_true", help="Run with actual API calls")
    args = parser.parse_args()
    
    if args.with_api:
        await test_evaluation()
    else:
        await test_without_api()

if __name__ == "__main__":
    asyncio.run(main())
