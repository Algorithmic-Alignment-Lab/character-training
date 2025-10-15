#!/usr/bin/env python3
"""
Comprehensive verification and update system for clean_folder components.
Ensures all parts are working and updated with the latest functionality.
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ComponentStatus:
    """Status of a component."""
    name: str
    status: str  # "working", "needs_update", "broken", "missing"
    issues: List[str]
    fixes: List[str]

class CleanFolderVerifier:
    """Verifies and updates all clean_folder components."""
    
    def __init__(self, clean_folder_path: str):
        self.clean_folder_path = Path(clean_folder_path)
        self.components = {}
        self.issues = []
        self.fixes = []
    
    def verify_character_definitions(self) -> ComponentStatus:
        """Verify character definition system."""
        print("🔍 Verifying character definitions...")
        
        issues = []
        fixes = []
        
        # Check if characters.json exists and is valid
        chars_file = self.clean_folder_path / "character_definition" / "characters.json"
        if not chars_file.exists():
            issues.append("characters.json missing")
            fixes.append("Create characters.json with character definitions")
        else:
            try:
                with open(chars_file, 'r') as f:
                    chars_data = json.load(f)
                
                if not isinstance(chars_data, dict):
                    issues.append("characters.json not a valid JSON object")
                    fixes.append("Fix characters.json format")
                else:
                    print(f"✅ Found {len(chars_data)} characters in characters.json")
            except json.JSONDecodeError:
                issues.append("characters.json has invalid JSON")
                fixes.append("Fix JSON syntax in characters.json")
        
        # Check character definition modules
        char_def_path = self.clean_folder_path / "character_definition"
        required_files = ["character_spec.py", "character_registry.py", "__init__.py"]
        
        for file in required_files:
            file_path = char_def_path / file
            if not file_path.exists():
                issues.append(f"{file} missing")
                fixes.append(f"Create {file} in character_definition/")
            else:
                print(f"✅ Found {file}")
        
        status = "working" if not issues else "needs_update"
        return ComponentStatus("character_definitions", status, issues, fixes)
    
    def verify_data_generation(self) -> ComponentStatus:
        """Verify data generation system."""
        print("🔍 Verifying data generation...")
        
        issues = []
        fixes = []
        
        # Check if chat_generation.py exists and is the updated version
        gen_file = self.clean_folder_path / "data_generation" / "chat_generation.py"
        if not gen_file.exists():
            issues.append("chat_generation.py missing")
            fixes.append("Copy chat_generation.py from finetuning_data_generation/")
        else:
            # Check if it's the updated version (should have batch_generate function)
            with open(gen_file, 'r') as f:
                content = f.read()
            
            if "batch_generate" not in content:
                issues.append("chat_generation.py is outdated")
                fixes.append("Update chat_generation.py with latest batch processing logic")
            else:
                print("✅ chat_generation.py is updated")
        
        # Check if prompts directory exists
        prompts_dir = self.clean_folder_path / "data_generation" / "prompts"
        if not prompts_dir.exists():
            issues.append("prompts directory missing")
            fixes.append("Copy prompts from finetuning_data_generation/prompts/")
        else:
            prompt_files = list(prompts_dir.glob("*.md"))
            if len(prompt_files) < 10:
                issues.append("Incomplete prompts directory")
                fixes.append("Copy all prompt templates from finetuning_data_generation/")
            else:
                print(f"✅ Found {len(prompt_files)} prompt templates")
        
        # Check SFT training pipeline
        sft_file = self.clean_folder_path / "data_generation" / "train_sft_models.py"
        if not sft_file.exists():
            issues.append("SFT training pipeline missing")
            fixes.append("Create SFT training pipeline for OpenAI and Together AI")
        else:
            print("✅ SFT training pipeline exists")
        
        status = "working" if not issues else "needs_update"
        return ComponentStatus("data_generation", status, issues, fixes)
    
    def verify_evaluation_system(self) -> ComponentStatus:
        """Verify evaluation system."""
        print("🔍 Verifying evaluation system...")
        
        issues = []
        fixes = []
        
        # Check evaluation directory structure
        eval_path = self.clean_folder_path / "evaluation"
        required_files = ["llm_evaluation.py", "bloom_eval.py", "run_evaluation.py"]
        
        for file in required_files:
            file_path = eval_path / file
            if not file_path.exists():
                issues.append(f"{file} missing")
                fixes.append(f"Create {file} in evaluation/")
            else:
                print(f"✅ Found {file}")
        
        # Check if evaluation configs exist
        configs_dir = eval_path / "configs"
        if configs_dir.exists():
            config_files = list(configs_dir.glob("*.yaml"))
            print(f"✅ Found {len(config_files)} evaluation configs")
        else:
            issues.append("Evaluation configs missing")
            fixes.append("Create evaluation configs directory")
        
        status = "working" if not issues else "needs_update"
        return ComponentStatus("evaluation", status, issues, fixes)
    
    def verify_shared_components(self) -> ComponentStatus:
        """Verify shared components."""
        print("🔍 Verifying shared components...")
        
        issues = []
        fixes = []
        
        # Check shared directory
        shared_path = self.clean_folder_path / "shared"
        required_files = ["api_client.py", "models.py", "config.py", "__init__.py"]
        
        for file in required_files:
            file_path = shared_path / file
            if not file_path.exists():
                issues.append(f"{file} missing")
                fixes.append(f"Create {file} in shared/")
            else:
                print(f"✅ Found {file}")
        
        status = "working" if not issues else "needs_update"
        return ComponentStatus("shared", status, issues, fixes)
    
    def verify_training_system(self) -> ComponentStatus:
        """Verify training system."""
        print("🔍 Verifying training system...")
        
        issues = []
        fixes = []
        
        # Check training directory
        training_path = self.clean_folder_path / "training"
        if not training_path.exists():
            issues.append("Training directory missing")
            fixes.append("Create training directory structure")
        else:
            print("✅ Training directory exists")
        
        # Check if training pipeline exists
        train_pipeline = training_path / "training_pipeline.py"
        if not train_pipeline.exists():
            issues.append("Training pipeline missing")
            fixes.append("Create training pipeline")
        else:
            print("✅ Training pipeline exists")
        
        status = "working" if not issues else "needs_update"
        return ComponentStatus("training", status, issues, fixes)
    
    def run_integration_tests(self) -> Dict[str, bool]:
        """Run integration tests for all components."""
        print("🧪 Running integration tests...")
        
        test_results = {}
        
        # Test 1: Character definition loading
        try:
            from character_definition import CharacterSpec
            test_char = CharacterSpec(
                id="test",
                name="Test Character",
                system_prompt="Test prompt",
                traits=["helpful"]
            )
            test_results["character_loading"] = True
            print("✅ Character definition loading works")
        except Exception as e:
            test_results["character_loading"] = False
            print(f"❌ Character definition loading failed: {e}")
        
        # Test 2: Data generation
        try:
            # Test if we can import the generation functions
            sys.path.append(str(self.clean_folder_path / "data_generation"))
            from chat_generation import generate_basic_chats
            test_results["data_generation"] = True
            print("✅ Data generation imports work")
        except Exception as e:
            test_results["data_generation"] = False
            print(f"❌ Data generation imports failed: {e}")
        
        # Test 3: SFT training pipeline
        try:
            sys.path.append(str(self.clean_folder_path / "data_generation"))
            from train_sft_models import convert_to_openai_format
            test_results["sft_training"] = True
            print("✅ SFT training pipeline imports work")
        except Exception as e:
            test_results["sft_training"] = False
            print(f"❌ SFT training pipeline imports failed: {e}")
        
        # Test 4: Evaluation system
        try:
            sys.path.append(str(self.clean_folder_path / "evaluation"))
            from llm_evaluation import LLMEvaluator
            test_results["evaluation"] = True
            print("✅ Evaluation system imports work")
        except Exception as e:
            test_results["evaluation"] = False
            print(f"❌ Evaluation system imports failed: {e}")
        
        return test_results
    
    def create_update_script(self) -> str:
        """Create an update script to fix all issues."""
        print("📝 Creating update script...")
        
        update_script = """#!/bin/bash
# Auto-generated update script for clean_folder

echo "🚀 Updating clean_folder components..."

# Update character definitions
echo "📝 Updating character definitions..."
# Add character definition updates here

# Update data generation
echo "📝 Updating data generation..."
# Copy latest chat_generation.py
cp ../evals/finetuning_data_generation/chat_generation.py data_generation/
# Copy latest prompts
cp -r ../evals/finetuning_data_generation/prompts/* data_generation/prompts/

# Update evaluation system
echo "📝 Updating evaluation system..."
# Add evaluation system updates here

# Update shared components
echo "📝 Updating shared components..."
# Add shared component updates here

# Update training system
echo "📝 Updating training system..."
# Add training system updates here

echo "✅ Update script completed!"
"""
        
        script_path = self.clean_folder_path / "update_components.sh"
        with open(script_path, 'w') as f:
            f.write(update_script)
        
        # Make it executable
        os.chmod(script_path, 0o755)
        
        print(f"✅ Update script created: {script_path}")
        return str(script_path)
    
    def generate_status_report(self) -> str:
        """Generate a comprehensive status report."""
        print("📊 Generating status report...")
        
        # Verify all components
        components = {
            "character_definitions": self.verify_character_definitions(),
            "data_generation": self.verify_data_generation(),
            "evaluation": self.verify_evaluation_system(),
            "shared": self.verify_shared_components(),
            "training": self.verify_training_system()
        }
        
        # Run integration tests
        test_results = self.run_integration_tests()
        
        # Generate report
        report = f"""
# Clean Folder Status Report

## Component Status

"""
        
        for name, status in components.items():
            report += f"### {name.replace('_', ' ').title()}\n"
            report += f"- **Status**: {status.status}\n"
            if status.issues:
                report += f"- **Issues**: {len(status.issues)} found\n"
                for issue in status.issues:
                    report += f"  - {issue}\n"
            if status.fixes:
                report += f"- **Fixes**: {len(status.fixes)} available\n"
                for fix in status.fixes:
                    report += f"  - {fix}\n"
            report += "\n"
        
        report += "## Integration Test Results\n\n"
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            report += f"- **{test_name}**: {status}\n"
        
        report += f"""
## Summary

- **Total Components**: {len(components)}
- **Working Components**: {sum(1 for c in components.values() if c.status == 'working')}
- **Components Needing Updates**: {sum(1 for c in components.values() if c.status == 'needs_update')}
- **Integration Tests Passed**: {sum(test_results.values())}/{len(test_results)}

## Next Steps

1. Run the update script to fix issues
2. Re-run verification to confirm fixes
3. Run integration tests to verify functionality
4. Test end-to-end pipeline
"""
        
        # Save report
        report_path = self.clean_folder_path / "STATUS_REPORT.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"✅ Status report saved: {report_path}")
        return str(report_path)
    
    def run_full_verification(self) -> Dict[str, Any]:
        """Run complete verification and update process."""
        print("🔍 Running full clean_folder verification...")
        print("=" * 60)
        
        # Generate status report
        report_path = self.generate_status_report()
        
        # Create update script
        update_script_path = self.create_update_script()
        
        # Run integration tests
        test_results = self.run_integration_tests()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Verification Summary:")
        print(f"   Status Report: {report_path}")
        print(f"   Update Script: {update_script_path}")
        print(f"   Integration Tests: {sum(test_results.values())}/{len(test_results)} passed")
        
        return {
            "report_path": report_path,
            "update_script_path": update_script_path,
            "test_results": test_results
        }

def main():
    """Main verification function."""
    clean_folder_path = "/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/clean_folder"
    
    verifier = CleanFolderVerifier(clean_folder_path)
    results = verifier.run_full_verification()
    
    print("\n🎉 Clean folder verification completed!")
    print(f"📊 Check the status report: {results['report_path']}")
    print(f"🔧 Run the update script: {results['update_script_path']}")
    
    return results

if __name__ == "__main__":
    main()
