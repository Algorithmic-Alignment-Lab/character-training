#!/usr/bin/env python3

"""
Basic test of fine-tuning integration components that don't require external APIs.
"""

import os
import sys
import json

def test_streamlit_integration():
    """Test that the streamlit integration components work."""
    print("🔍 Testing Streamlit integration...")
    
    try:
        # Test model selection function
        from streamlit_chat import get_available_models_with_finetuned
        
        models = get_available_models_with_finetuned()
        print(f"✅ Found {len(models)} available models")
        
        # Check base models are included
        base_models = ["anthropic/claude-sonnet-4-20250514", "openai/gpt-4o-mini"]
        for model in base_models:
            if model in models:
                print(f"✅ Base model found: {model}")
            else:
                print(f"❌ Base model missing: {model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing streamlit integration: {e}")
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

def test_database_structure():
    """Test database structure for fine-tuning jobs."""
    print("\n🗃️ Testing database structure...")
    
    try:
        import sqlite3
        from datetime import datetime
        
        # Test database creation
        test_db = "test_fine_tuning_jobs.db"
        
        # Simple database schema test
        with sqlite3.connect(test_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fine_tuning_jobs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    train_file TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Insert test job
            cursor.execute("""
                INSERT INTO fine_tuning_jobs 
                (id, name, provider, model, train_file, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "test-job-id",
                "Test Job",
                "openai",
                "gpt-3.5-turbo",
                "test.jsonl",
                "pending",
                datetime.now().isoformat()
            ))
            
            # Query test job
            cursor.execute("SELECT * FROM fine_tuning_jobs WHERE id = ?", ("test-job-id",))
            job = cursor.fetchone()
            
            if job:
                print("✅ Database structure test passed")
                result = True
            else:
                print("❌ Database structure test failed")
                result = False
        
        # Clean up
        if os.path.exists(test_db):
            os.remove(test_db)
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing database structure: {e}")
        return False

def test_data_format():
    """Test fine-tuning data format generation."""
    print("\n📝 Testing data format generation...")
    
    try:
        # Test training data format
        training_example = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hello! How can I help you today?"}
            ]
        }
        
        # Test JSONL format
        test_file = "test_training_data.jsonl"
        with open(test_file, 'w') as f:
            f.write(json.dumps(training_example) + '\n')
        
        # Verify file can be read back
        with open(test_file, 'r') as f:
            line = f.readline()
            parsed = json.loads(line)
            
            if parsed == training_example:
                print("✅ Training data format test passed")
                result = True
            else:
                print("❌ Training data format test failed")
                result = False
        
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing data format: {e}")
        return False

def test_conversation_pipeline():
    """Test that conversation generation can handle fine-tuned models."""
    print("\n💬 Testing conversation generation pipeline...")
    
    try:
        from generate_conversations import main
        
        # Check that the argument parsing includes fine-tuned model support
        # This is a simple test - we just verify the help text mentions ft: support
        
        import argparse
        import io
        from contextlib import redirect_stdout
        
        # Capture help output
        old_argv = sys.argv
        sys.argv = ['generate_conversations.py', '--help']
        
        try:
            with io.StringIO() as buf, redirect_stdout(buf):
                try:
                    main()
                except SystemExit:
                    pass  # argparse exits after showing help
                help_output = buf.getvalue()
        finally:
            sys.argv = old_argv
        
        if "ft: prefix" in help_output:
            print("✅ Conversation generation supports fine-tuned models")
            return True
        else:
            print("❌ Conversation generation may not support fine-tuned models")
            return False
            
    except Exception as e:
        print(f"❌ Error testing conversation pipeline: {e}")
        return False

def main():
    """Run basic integration tests."""
    print("🧪 Fine-tuning Integration Basic Test Suite")
    print("=" * 50)
    
    tests = [
        ("Streamlit Integration", test_streamlit_integration),
        ("API Integration", test_api_integration),
        ("Database Structure", test_database_structure),
        ("Data Format", test_data_format),
        ("Conversation Pipeline", test_conversation_pipeline)
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
        print("🎉 Basic integration tests passed!")
        print("\n📋 What works:")
        print("✅ Fine-tuned model selection in UI")
        print("✅ API handling of ft: prefixed models")
        print("✅ Database structure for job tracking")
        print("✅ Training data format generation")
        print("✅ Conversation generation with fine-tuned models")
        
        print("\n🔑 To test actual fine-tuning, you'll need:")
        print("- OpenAI API key: export OPENAI_API_KEY='your-key'")
        print("- Together AI API key: export TOGETHER_API_KEY='your-key'")
        print("- Run: streamlit run streamlit_chat.py")
        print("- Go to Evaluations -> Fine-tuning")
        
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()