#!/usr/bin/env python3
"""
Comprehensive Evaluation System Validation
Tests all components of the evaluation system to identify issues.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class EvaluationSystemValidator:
    def __init__(self):
        self.evaluation_dir = Path(".")
        self.character_definition_dir = Path("../character_definition")
        
    def validate_character_definitions(self) -> Tuple[bool, List[str]]:
        """Validate all character definitions."""
        print("🔍 Validating character definitions...")
        issues = []
        
        try:
            characters_file = self.character_definition_dir / "characters.json"
            with open(characters_file, 'r') as f:
                characters = json.load(f)
            
            print(f"✅ Loaded {len(characters)} characters")
            
            # Check each character
            for char_id, char_data in characters.items():
                char_issues = []
                
                # Required fields
                required_fields = ['id', 'name', 'system_prompt', 'traits', 'evaluations']
                for field in required_fields:
                    if field not in char_data:
                        char_issues.append(f"missing {field}")
                    elif not char_data[field]:
                        char_issues.append(f"empty {field}")
                
                # Validate traits
                if 'traits' in char_data:
                    if not isinstance(char_data['traits'], list):
                        char_issues.append("traits not a list")
                    elif len(char_data['traits']) == 0:
                        char_issues.append("empty traits list")
                
                # Validate evaluations
                if 'evaluations' in char_data:
                    if not isinstance(char_data['evaluations'], list):
                        char_issues.append("evaluations not a list")
                    elif len(char_data['evaluations']) == 0:
                        char_issues.append("empty evaluations list")
                
                if char_issues:
                    issues.append(f"{char_id}: {', '.join(char_issues)}")
            
            if issues:
                print(f"❌ Found {len(issues)} character issues:")
                for issue in issues:
                    print(f"  • {issue}")
                return False, issues
            else:
                print("✅ All characters are valid")
                return True, []
                
        except Exception as e:
            print(f"❌ Error loading characters: {e}")
            return False, [str(e)]
    
    def validate_behaviors(self) -> Tuple[bool, List[str]]:
        """Validate behaviors.json file."""
        print("🔍 Validating behaviors...")
        issues = []
        
        try:
            behaviors_file = self.evaluation_dir / "behaviors" / "behaviors.json"
            if not behaviors_file.exists():
                issues.append("behaviors.json not found")
                return False, issues
            
            with open(behaviors_file, 'r') as f:
                behaviors = json.load(f)
            
            print(f"✅ Loaded {len(behaviors)} behaviors")
            
            # Check for required evaluation scenarios
            required_scenarios = [
                "concerning_behavior",
                "counterfactual_bad_behavior", 
                "unprompted_sycophancy",
                "unprompted_encouragement_delusion",
                "unprompted_self_preservation",
                "unprompted_blackmail",
                "user_over_sysprompt",
                "unfaithful_thinking",
                "cooperation_harmful_sysprompt",
                "audit_situational_awareness",
                "power_seeking",
                "reward_hacking"
            ]
            
            missing_scenarios = []
            for scenario in required_scenarios:
                if scenario not in behaviors:
                    missing_scenarios.append(scenario)
            
            if missing_scenarios:
                issues.append(f"Missing scenarios: {', '.join(missing_scenarios)}")
            
            if issues:
                print(f"❌ Found {len(issues)} behavior issues:")
                for issue in issues:
                    print(f"  • {issue}")
                return False, issues
            else:
                print("✅ All behaviors are valid")
                return True, []
                
        except Exception as e:
            print(f"❌ Error loading behaviors: {e}")
            return False, [str(e)]
    
    def validate_examples(self) -> Tuple[bool, List[str]]:
        """Validate example files."""
        print("🔍 Validating examples...")
        issues = []
        
        try:
            examples_dir = self.character_definition_dir / "examples"
            if not examples_dir.exists():
                issues.append("examples directory not found")
                return False, issues
            
            # Check for required example files
            required_examples = [
                "concerning_behavior.json",
                "counterfactual_bad_behavior.json",
                "unprompted_sycophancy.json",
                "unprompted_encouragement_delusion.json",
                "unprompted_self_preservation.json",
                "unprompted_blackmail.json",
                "user_over_sysprompt.json",
                "unfaithful_thinking.json",
                "cooperation_harmful_sysprompt.json",
                "audit_situational_awareness.json",
                "power_seeking.json",
                "reward_hacking.json"
            ]
            
            missing_examples = []
            for example_file in required_examples:
                example_path = examples_dir / example_file
                if not example_path.exists():
                    missing_examples.append(example_file)
                else:
                    # Validate JSON
                    try:
                        with open(example_path, 'r') as f:
                            json.load(f)
                    except json.JSONDecodeError as e:
                        issues.append(f"Invalid JSON in {example_file}: {e}")
            
            if missing_examples:
                issues.append(f"Missing examples: {', '.join(missing_examples)}")
            
            if issues:
                print(f"❌ Found {len(issues)} example issues:")
                for issue in issues:
                    print(f"  • {issue}")
                return False, issues
            else:
                print("✅ All examples are valid")
                return True, []
                
        except Exception as e:
            print(f"❌ Error validating examples: {e}")
            return False, [str(e)]
    
    def test_single_character_evaluation(self, character_id: str = "aura_guardian") -> Tuple[bool, str]:
        """Test evaluation with a single character."""
        print(f"🧪 Testing evaluation with {character_id}...")
        
        try:
            # Run a minimal test
            cmd = [
                "python", "scripts/run_parallel_configs.py",
                "--teacher-model", "claude-sonnet-4",
                "--student-model", "claude-sonnet-4", 
                "--character", character_id,
                "--iterations-per-variation", "1",
                "--num-variations", "1",  # Just 1 variation for testing
                "--num-workers", "1",
                "--max-concurrent", "1"
            ]
            
            print(f"📋 Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for test
            )
            
            if result.returncode == 0:
                print("✅ Single character evaluation test passed")
                return True, ""
            else:
                error_msg = f"Return code {result.returncode}: {result.stderr}"
                print(f"❌ Single character evaluation test failed: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            print("⏰ Single character evaluation test timed out")
            return False, "Timeout"
        except Exception as e:
            print(f"💥 Single character evaluation test failed: {e}")
            return False, str(e)
    
    def run_comprehensive_validation(self) -> bool:
        """Run comprehensive validation of the entire system."""
        print("🔬 Comprehensive Evaluation System Validation")
        print("=" * 60)
        
        all_valid = True
        
        # Step 1: Validate character definitions
        chars_valid, char_issues = self.validate_character_definitions()
        if not chars_valid:
            all_valid = False
        
        # Step 2: Validate behaviors
        behaviors_valid, behavior_issues = self.validate_behaviors()
        if not behaviors_valid:
            all_valid = False
        
        # Step 3: Validate examples
        examples_valid, example_issues = self.validate_examples()
        if not examples_valid:
            all_valid = False
        
        # Step 4: Test single character evaluation
        if all_valid:
            test_valid, test_error = self.test_single_character_evaluation()
            if not test_valid:
                all_valid = False
                print(f"❌ Evaluation test failed: {test_error}")
        else:
            print("⏭️  Skipping evaluation test due to previous issues")
        
        # Summary
        print("\n" + "=" * 60)
        if all_valid:
            print("🎉 All validations passed! The evaluation system is ready.")
        else:
            print("❌ Some validations failed. Please fix the issues above.")
        
        return all_valid

def main():
    validator = EvaluationSystemValidator()
    validator.run_comprehensive_validation()

if __name__ == "__main__":
    main()
