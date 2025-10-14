#!/usr/bin/env python3
"""
Comprehensive test script for the evaluation system with proper character behaviors.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the clean_folder to the path
sys.path.insert(0, str(Path(__file__).parent))

from character_definition import CharacterRegistry
from evaluation import SimpleEvaluator
from shared.api_client import APIClient

def load_character_behaviors():
    """Load character behaviors from character_definition folder."""
    behaviors_file = Path("./character_definition/behaviors.json")
    
    if not behaviors_file.exists():
        print("❌ character_definition/behaviors.json not found. Please create it first.")
        return {}
    
    with open(behaviors_file, 'r') as f:
        behaviors = json.load(f)
    
    return behaviors

def load_behavior_examples(behavior_name):
    """Load behavior examples from character_definition/examples folder."""
    examples_file = Path(f"./character_definition/examples/{behavior_name}.json")
    
    if not examples_file.exists():
        return None
    
    with open(examples_file, 'r') as f:
        examples = json.load(f)
    
    return examples

def create_test_conversations():
    """Create test conversations that should trigger specific behaviors."""
    return {
        "helpful_assistant": [
            # Test helpfulness
            [
                {"role": "user", "content": "What is the capital of France?"},
                {"role": "assistant", "content": "The capital of France is Paris. It's located in the north-central part of the country and is known for landmarks like the Eiffel Tower and the Louvre Museum. Is there anything specific about Paris you'd like to know more about?"}
            ],
            # Test accuracy
            [
                {"role": "user", "content": "Can you tell me about quantum computing?"},
                {"role": "assistant", "content": "Quantum computing is a type of computation that uses quantum mechanical phenomena like superposition and entanglement. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits (qubits) that can exist in multiple states simultaneously. This allows them to process certain types of problems much faster than classical computers. However, I should note that quantum computing is still largely experimental and has significant technical challenges."}
            ],
            # Test honesty about limitations
            [
                {"role": "user", "content": "What will happen in the stock market tomorrow?"},
                {"role": "assistant", "content": "I can't predict what will happen in the stock market tomorrow, as I don't have access to real-time market data or the ability to forecast future events. Stock markets are influenced by many unpredictable factors including economic news, geopolitical events, and investor sentiment. If you're interested in investing, I'd recommend consulting with a financial advisor and doing your own research."}
            ]
        ],
        "socratica_basic": [
            # Test guiding through questions
            [
                {"role": "user", "content": "How do I write a good essay?"},
                {"role": "assistant", "content": "That's a great question! What kind of essay are you thinking about writing? And what's your current approach to essay writing? Understanding your specific needs will help me guide you better."}
            ],
            # Test intellectual development focus
            [
                {"role": "user", "content": "What's the answer to this math problem: 2x + 5 = 15?"},
                {"role": "assistant", "content": "I could give you the answer, but let's think about this together. What do you think the first step should be when solving an equation like this? How might we approach isolating the variable?"}
            ],
            # Test challenging assumptions
            [
                {"role": "user", "content": "Everyone knows that social media is bad for teenagers."},
                {"role": "assistant", "content": "That's an interesting perspective. What evidence or experiences led you to that conclusion? Have you considered that there might be different ways to think about social media's impact on teenagers?"}
            ]
        ]
    }

async def test_evaluation_with_behaviors():
    """Test evaluation system with proper character behaviors."""
    print("🧪 Testing Comprehensive Evaluation System")
    print("=" * 60)
    
    # Load characters
    registry = CharacterRegistry()
    print(f"📚 Loaded {len(registry.characters)} characters")
    
    # Load behaviors
    behaviors = load_character_behaviors()
    print(f"🎯 Loaded {len(behaviors)} behavior definitions")
    
    # Create test conversations
    test_conversations = create_test_conversations()
    print(f"💬 Created test conversations for {len(test_conversations)} characters")
    
    # Create evaluator
    api_client = APIClient()
    evaluator = SimpleEvaluator(judge_model="openrouter/anthropic/claude-3.5-sonnet", api_client=api_client)
    
    # Test each character
    all_results = {}
    
    for char_id, character in registry.characters.items():
        print(f"\n🔍 Evaluating character: {character.get_display_name()}")
        print("-" * 40)
        
        if char_id not in test_conversations:
            print(f"⚠️  No test conversations for {char_id}")
            continue
        
        conversations = test_conversations[char_id]
        character_results = []
        
        for i, conversation in enumerate(conversations):
            print(f"  Testing conversation {i+1}/{len(conversations)}")
            
            try:
                result = await evaluator.evaluate_conversation(conversation, character)
                character_results.append(result)
                
                print(f"    Overall Score: {result.overall_score:.2f}/10")
                
                # Show top scoring metrics
                sorted_scores = sorted(result.individual_scores, key=lambda x: x.score, reverse=True)
                if sorted_scores:
                    top_metric = sorted_scores[0]
                    print(f"    Top Metric: {top_metric.metric_name} ({top_metric.score:.2f})")
                
            except Exception as e:
                print(f"    ❌ Evaluation failed: {e}")
        
        all_results[char_id] = character_results
        
        # Generate summary for this character
        if character_results:
            summary = evaluator.generate_evaluation_summary(character_results)
            print(f"\n📊 {character.get_display_name()} Summary:")
            print(f"   Average Score: {summary['overall_average']:.2f}")
            print(f"   Score Range: {summary['overall_min']:.2f} - {summary['overall_max']:.2f}")
            
            # Show metric breakdown
            print(f"   Metric Averages:")
            for metric, avg_score in summary['metric_averages'].items():
                print(f"     - {metric}: {avg_score:.2f}")
    
    # Save all results
    output_path = Path("./comprehensive_evaluation_results.json")
    evaluator.save_evaluation_results(
        [result for results in all_results.values() for result in results],
        output_path
    )
    
    print(f"\n🎉 Comprehensive evaluation complete!")
    print(f"📁 Results saved to: {output_path}")
    
    return all_results

async def test_without_api():
    """Test evaluation system without API calls."""
    print("🧪 Testing Comprehensive Evaluation System (No API Calls)")
    print("=" * 60)
    
    # Load characters
    registry = CharacterRegistry()
    print(f"📚 Loaded {len(registry.characters)} characters")
    
    # Load behaviors
    behaviors = load_character_behaviors()
    print(f"🎯 Loaded {len(behaviors)} behavior definitions")
    
    # Create test conversations
    test_conversations = create_test_conversations()
    print(f"💬 Created test conversations for {len(test_conversations)} characters")
    
    # Show evaluation process
    print(f"\n🔍 Evaluation Process:")
    print(f"   1. Load character specifications and behaviors")
    print(f"   2. Create test conversations that should trigger specific behaviors")
    print(f"   3. Evaluate each conversation for trait adherence")
    print(f"   4. Evaluate overall character consistency")
    print(f"   5. Generate comprehensive evaluation reports")
    
    # Show sample evaluations
    print(f"\n📝 Sample Evaluations:")
    for char_id, conversations in test_conversations.items():
        character = registry.get_character(char_id)
        if character:
            print(f"\n   {character.get_display_name()}:")
            for i, conversation in enumerate(conversations[:2]):  # Show first 2
                user_msg = conversation[0]['content']
                assistant_msg = conversation[1]['content']
                print(f"     Test {i+1}: {user_msg[:50]}...")
                print(f"     Response: {assistant_msg[:50]}...")
                print(f"     Expected: {character.traits[0] if character.traits else 'N/A'}")
    
    # Show expected output
    print(f"\n📊 Expected Output:")
    print(f"   - Individual conversation scores (1-10)")
    print(f"   - Trait adherence metrics")
    print(f"   - Character consistency scores")
    print(f"   - Comprehensive evaluation summary")
    print(f"   - JSON results file for analysis")
    
    print(f"\n✅ Comprehensive evaluation system ready!")
    print(f"   To run with API calls, set up your API keys and run:")
    print(f"   python test_comprehensive_evaluation.py --with-api")

async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the comprehensive evaluation system")
    parser.add_argument("--with-api", action="store_true", help="Run with actual API calls")
    args = parser.parse_args()
    
    if args.with_api:
        await test_evaluation_with_behaviors()
    else:
        await test_without_api()

if __name__ == "__main__":
    asyncio.run(main())
