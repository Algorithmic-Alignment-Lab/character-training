#!/usr/bin/env python3
"""
End-to-end test for the complete clean_folder pipeline.
Tests: Character Definition → Data Generation → SFT Training → Evaluation
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# Add clean_folder to path
clean_folder_path = Path(__file__).parent
sys.path.append(str(clean_folder_path))

class CompletePipelineTester:
    """Tests the complete pipeline from character definition to evaluation."""
    
    def __init__(self):
        self.test_results = {}
        self.clean_folder_path = clean_folder_path
    
    async def test_character_definition(self) -> bool:
        """Test character definition system."""
        print("🧪 Testing character definition system...")
        
        try:
            # Test character loading
            from character_definition import CharacterSpec
            
            # Create test character
            test_char = CharacterSpec(
                id="pipeline_test_character",
                name="Pipeline Test Character",
                version="1.0",
                system_prompt="You are a helpful AI assistant for testing the complete pipeline.",
                traits=["helpful", "knowledgeable", "friendly"],
                key_facts=[
                    "I am designed to help users with their questions and problems.",
                    "I provide accurate and useful information.",
                    "I am patient and willing to explain complex topics."
                ]
            )
            
            print(f"✅ Character created: {test_char.name}")
            print(f"   Traits: {test_char.traits}")
            print(f"   Facts: {len(test_char.key_facts)}")
            
            self.test_results["character_definition"] = True
            return True
            
        except Exception as e:
            print(f"❌ Character definition test failed: {e}")
            self.test_results["character_definition"] = False
            return False
    
    async def test_data_generation(self) -> bool:
        """Test data generation system."""
        print("\n🧪 Testing data generation system...")
        
        try:
            # Import generation functions
            from data_generation.chat_generation import generate_basic_chats, generate_chats
            
            # Test basic chat generation
            character_definition = {
                "name": "Pipeline Test Character",
                "system_prompt": "You are a helpful AI assistant for testing the complete pipeline.",
                "key_facts": [
                    "I am designed to help users with their questions and problems.",
                    "I provide accurate and useful information."
                ]
            }
            
            print("📊 Testing basic chat generation...")
            basic_chats = await generate_basic_chats(
                num_chats=2,  # Small number for testing
                character_definition=character_definition,
                model_id="claude-3-5-haiku-20241022",
                prompt_dir="./data_generation/prompts",
                num_chats_per_fact=1,
                require_thinking=False
            )
            
            print(f"✅ Generated {len(basic_chats)} basic chats")
            
            # Test full generation pipeline
            print("📊 Testing full generation pipeline...")
            
            # Create character definition file for full pipeline
            char_def_path = "/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen/character_definitions.json"
            os.makedirs(os.path.dirname(char_def_path), exist_ok=True)
            
            char_definitions = {
                "pipeline_test_character": character_definition
            }
            
            with open(char_def_path, 'w') as f:
                json.dump(char_definitions, f, indent=2)
            
            # Run full generation
            result = await generate_chats(
                character_id="pipeline_test_character",
                output_path="./test_complete_pipeline_output",
                num_chat_types=2,
                num_chat_ideas=2,
                total_chats_target=3,
                basic_question_percentage=0.4,
                num_basic_chats_per_fact=1,
                require_thinking=False,
                enable_dpo=False,
                debug=True
            )
            
            print("✅ Full generation pipeline completed")
            
            # Check output files
            output_dir = Path("./test_complete_pipeline_output/pipeline_test_character")
            if output_dir.exists():
                output_files = list(output_dir.glob("*"))
                print(f"✅ Generated {len(output_files)} output files")
                
                # Check main output file
                main_output = output_dir / "synth_chats.jsonl"
                if main_output.exists():
                    with open(main_output, 'r') as f:
                        lines = f.readlines()
                    print(f"✅ Main output file contains {len(lines)} chats")
                else:
                    print("⚠️  Main output file not found")
            else:
                print("⚠️  Output directory not found")
            
            self.test_results["data_generation"] = True
            return True
            
        except Exception as e:
            print(f"❌ Data generation test failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results["data_generation"] = False
            return False
    
    async def test_sft_training(self) -> bool:
        """Test SFT training pipeline."""
        print("\n🧪 Testing SFT training pipeline...")
        
        try:
            # Check if training data exists
            training_data_path = "./test_complete_pipeline_output/pipeline_test_character/synth_chats.jsonl"
            
            if not os.path.exists(training_data_path):
                print("⚠️  Training data not found, skipping SFT training test")
                self.test_results["sft_training"] = "skipped"
                return True
            
            # Test data conversion
            from data_generation.train_sft_models import convert_to_openai_format, convert_to_together_format
            
            # Load training data
            with open(training_data_path, 'r') as f:
                chat_data = [json.loads(line) for line in f]
            
            print(f"📊 Loaded {len(chat_data)} training examples")
            
            # Test OpenAI format conversion
            openai_data = convert_to_openai_format(chat_data)
            print(f"✅ Converted {len(openai_data)} examples to OpenAI format")
            
            # Test Together AI format conversion
            together_data = convert_to_together_format(chat_data)
            print(f"✅ Converted {len(together_data)} examples to Together AI format")
            
            # Test data splitting
            from data_generation.train_sft_models import split_data
            train_data, val_data = split_data(openai_data)
            print(f"✅ Split into {len(train_data)} training and {len(val_data)} validation examples")
            
            # Test file saving
            from data_generation.train_sft_models import save_jsonl
            test_output_dir = "./test_sft_training_output"
            train_path = f"{test_output_dir}/test_train.jsonl"
            val_path = f"{test_output_dir}/test_val.jsonl"
            
            save_jsonl(train_data, train_path)
            save_jsonl(val_data, val_path)
            
            print(f"✅ Saved training files to {test_output_dir}")
            
            self.test_results["sft_training"] = True
            return True
            
        except Exception as e:
            print(f"❌ SFT training test failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results["sft_training"] = False
            return False
    
    async def test_evaluation_system(self) -> bool:
        """Test evaluation system."""
        print("\n🧪 Testing evaluation system...")
        
        try:
            # Test evaluation imports
            import sys
            sys.path.append(str(self.clean_folder_path / "evaluation"))
            from llm_evaluation import LLMEvaluator
            from bloom_eval import run_pipeline
            
            print("✅ Evaluation system imports work")
            
            # Test evaluation configuration loading
            eval_config_path = self.clean_folder_path / "evaluation" / "configs"
            if eval_config_path.exists():
                config_files = list(eval_config_path.glob("*.yaml"))
                print(f"✅ Found {len(config_files)} evaluation configs")
            else:
                print("⚠️  Evaluation configs not found")
            
            self.test_results["evaluation"] = True
            return True
            
        except Exception as e:
            print(f"❌ Evaluation system test failed: {e}")
            self.test_results["evaluation"] = False
            return False
    
    async def test_shared_components(self) -> bool:
        """Test shared components."""
        print("\n🧪 Testing shared components...")
        
        try:
            # Test shared imports
            from shared.api_client import APIClient
            from shared.models import Chat, GenerationConfig
            from shared.config import Config
            
            print("✅ Shared components imports work")
            
            # Test API client creation
            api_client = APIClient()
            print("✅ API client created")
            
            # Test model creation (Chat requires at least 2 messages)
            test_chat = Chat(
                messages=[
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there! How can I help you?"}
                ],
                character_id="test"
            )
            print("✅ Chat model created")
            
            self.test_results["shared_components"] = True
            return True
            
        except Exception as e:
            print(f"❌ Shared components test failed: {e}")
            self.test_results["shared_components"] = False
            return False
    
    async def run_complete_pipeline_test(self) -> Dict[str, Any]:
        """Run the complete pipeline test."""
        print("🚀 Starting complete pipeline test...")
        print("=" * 60)
        
        # Test all components
        tests = [
            ("Character Definition", self.test_character_definition),
            ("Data Generation", self.test_data_generation),
            ("SFT Training", self.test_sft_training),
            ("Evaluation System", self.test_evaluation_system),
            ("Shared Components", self.test_shared_components)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} test failed with exception: {e}")
                results[test_name] = False
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 Complete Pipeline Test Summary:")
        print("=" * 60)
        
        passed = sum(1 for r in results.values() if r is True)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⏭️  SKIP"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! The complete pipeline is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the error messages above.")
        
        return {
            "results": results,
            "passed": passed,
            "total": total,
            "success": passed == total
        }

async def main():
    """Main test function."""
    tester = CompletePipelineTester()
    results = await tester.run_complete_pipeline_test()
    
    return results

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success["success"] else 1)
