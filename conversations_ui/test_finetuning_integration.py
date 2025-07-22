#!/usr/bin/env python3

"""
Test script for fine-tuning integration with conversations_ui.
This script demonstrates how to:
1. Create fine-tuning data from conversations
2. Create a fine-tuning job
3. Test the fine-tuned model in the evaluation pipeline
"""

import os
import json
import asyncio
from fine_tuning_manager import FinetuningManager
from database import init_db, get_conversations


def test_data_generation():
    """Test generating fine-tuning data from conversations database."""
    print("🔍 Testing fine-tuning data generation...")
    
    # Initialize fine-tuning manager
    ft_manager = FinetuningManager()
    
    # Check if we have a conversations database
    db_path = "conversations.db"
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found. Please run some conversations first.")
        return False
    
    # Generate training data
    output_file = "test_training_data.jsonl"
    result = ft_manager.generate_finetuning_data_from_conversations(
        db_path, 
        output_file, 
        max_conversations=5
    )
    
    print(f"✅ {result}")
    
    # Verify the generated file
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            lines = f.readlines()
            print(f"📝 Generated {len(lines)} training examples")
            
            # Show first example
            if lines:
                example = json.loads(lines[0])
                print("📋 Sample training example:")
                print(json.dumps(example, indent=2))
        
        # Clean up
        os.remove(output_file)
        return True
    else:
        print("❌ Training data file was not created")
        return False


def test_job_creation():
    """Test creating a fine-tuning job."""
    print("\n🚀 Testing fine-tuning job creation...")
    
    ft_manager = FinetuningManager()
    
    # Create a mock training file
    training_data = [
        {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hello! How can I help you today?"}
            ]
        }
    ]
    
    train_file = "mock_training_data.jsonl"
    with open(train_file, 'w') as f:
        for example in training_data:
            f.write(json.dumps(example) + '\n')
    
    try:
        # Create a test job (using Together as it's more accessible)
        job = ft_manager.create_together_job(
            name="Test Fine-tuning Job",
            model="NousResearch/Llama-2-7b-hf",  # Example model
            train_file=train_file,
            n_epochs=1,
            batch_size=4,
            learning_rate=1e-5
        )
        
        print(f"✅ Created fine-tuning job: {job.name}")
        print(f"📋 Job ID: {job.id}")
        print(f"📋 Status: {job.status}")
        
        # Test listing jobs
        jobs = ft_manager.list_jobs()
        print(f"📊 Total jobs in database: {len(jobs)}")
        
        # Clean up
        ft_manager.delete_job(job.id)
        os.remove(train_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating job: {e}")
        if os.path.exists(train_file):
            os.remove(train_file)
        return False


def test_model_selection():
    """Test the model selection with fine-tuned models."""
    print("\n🎯 Testing model selection with fine-tuned models...")
    
    try:
        # Import the function from streamlit_chat
        from streamlit_chat import get_available_models_with_finetuned
        
        models = get_available_models_with_finetuned()
        print(f"📋 Available models: {len(models)}")
        
        # Check if base models are included
        base_models = ["anthropic/claude-sonnet-4-20250514", "openai/gpt-4o-mini"]
        for model in base_models:
            if model in models:
                print(f"✅ Base model found: {model}")
            else:
                print(f"❌ Base model missing: {model}")
        
        # Check for fine-tuned models (if any)
        ft_models = [m for m in models if m.startswith("ft:")]
        if ft_models:
            print(f"🤖 Fine-tuned models found: {len(ft_models)}")
            for model in ft_models:
                print(f"  - {model}")
        else:
            print("ℹ️ No fine-tuned models found (this is expected for new setups)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing model selection: {e}")
        return False


def test_api_integration():
    """Test LLM API integration with fine-tuned models."""
    print("\n🔗 Testing LLM API integration...")
    
    try:
        from llm_api import process_model_name
        
        # Test model name processing
        test_cases = [
            ("anthropic/claude-sonnet-4-20250514", "anthropic/claude-sonnet-4-20250514"),
            ("ft:gpt-3.5-turbo:my-org:custom-model", "gpt-3.5-turbo:my-org:custom-model"),
            ("ft:my-fine-tuned-model", "my-fine-tuned-model"),
            ("regular-model", "regular-model")
        ]
        
        all_passed = True
        for input_model, expected in test_cases:
            result = process_model_name(input_model)
            if result == expected:
                print(f"✅ {input_model} -> {result}")
            else:
                print(f"❌ {input_model} -> {result} (expected: {expected})")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing API integration: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🧪 Fine-tuning Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Data Generation", test_data_generation),
        ("Job Creation", test_job_creation),
        ("Model Selection", test_model_selection),
        ("API Integration", test_api_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Fine-tuning integration is working correctly.")
        print("\n📋 Next steps:")
        print("1. Run the Streamlit app: streamlit run streamlit_chat.py")
        print("2. Go to the Evaluations tab -> Fine-tuning")
        print("3. Create training data from your conversations")
        print("4. Create and run fine-tuning jobs")
        print("5. Test fine-tuned models in the Chat Interface")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()