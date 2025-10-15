#!/usr/bin/env python3
"""
Automated update script for all clean_folder components.
Ensures all parts are working and updated with the latest functionality.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any

class CleanFolderUpdater:
    """Updates all clean_folder components to ensure they're working."""
    
    def __init__(self, clean_folder_path: str):
        self.clean_folder_path = Path(clean_folder_path)
        self.root_path = self.clean_folder_path.parent
        self.updates_applied = []
        self.errors = []
    
    def update_data_generation(self) -> bool:
        """Update data generation components."""
        print("📝 Updating data generation components...")
        
        try:
            # Copy latest chat_generation.py from finetuning_data_generation
            source_file = self.root_path / "evals" / "finetuning_data_generation" / "chat_generation.py"
            target_file = self.clean_folder_path / "data_generation" / "chat_generation.py"
            
            if source_file.exists():
                shutil.copy2(source_file, target_file)
                print("✅ Updated chat_generation.py")
                self.updates_applied.append("chat_generation.py")
            else:
                print("⚠️  Source chat_generation.py not found")
                return False
            
            # Copy prompts directory
            source_prompts = self.root_path / "evals" / "finetuning_data_generation" / "prompts"
            target_prompts = self.clean_folder_path / "data_generation" / "prompts"
            
            if source_prompts.exists():
                if target_prompts.exists():
                    shutil.rmtree(target_prompts)
                shutil.copytree(source_prompts, target_prompts)
                print("✅ Updated prompts directory")
                self.updates_applied.append("prompts/")
            else:
                print("⚠️  Source prompts directory not found")
                return False
            
            # Ensure SFT training files exist
            sft_files = [
                "train_sft_models.py",
                "sft_training_pipeline.py", 
                "test_sft_conversion.py",
                "SFT_TRAINING_README.md"
            ]
            
            for file in sft_files:
                file_path = self.clean_folder_path / "data_generation" / file
                if not file_path.exists():
                    print(f"⚠️  {file} missing - this should have been created earlier")
                else:
                    print(f"✅ {file} exists")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating data generation: {e}")
            self.errors.append(f"data_generation: {e}")
            return False
    
    def update_character_definitions(self) -> bool:
        """Update character definition components."""
        print("📝 Updating character definitions...")
        
        try:
            # Check if characters.json exists and is valid
            chars_file = self.clean_folder_path / "character_definition" / "characters.json"
            
            if not chars_file.exists():
                print("⚠️  characters.json not found - creating from examples")
                
                # Load example characters
                examples_dir = self.clean_folder_path / "character_definition" / "examples"
                if examples_dir.exists():
                    example_files = list(examples_dir.glob("*.json"))
                    print(f"📊 Found {len(example_files)} example characters")
                    
                    # Create characters.json from examples
                    characters = {}
                    for example_file in example_files[:5]:  # Use first 5 examples
                        try:
                            with open(example_file, 'r') as f:
                                char_data = json.load(f)
                            
                            char_id = example_file.stem
                            characters[char_id] = char_data
                            
                        except Exception as e:
                            print(f"⚠️  Could not load {example_file}: {e}")
                    
                    # Save characters.json
                    with open(chars_file, 'w') as f:
                        json.dump(characters, f, indent=2)
                    
                    print(f"✅ Created characters.json with {len(characters)} characters")
                    self.updates_applied.append("characters.json")
                else:
                    print("⚠️  No example characters found")
                    return False
            else:
                print("✅ characters.json exists")
            
            # Check character definition modules
            char_def_path = self.clean_folder_path / "character_definition"
            required_files = ["character_spec.py", "character_registry.py", "__init__.py"]
            
            for file in required_files:
                file_path = char_def_path / file
                if not file_path.exists():
                    print(f"⚠️  {file} missing - creating basic version")
                    
                    if file == "character_spec.py":
                        self.create_character_spec_file(file_path)
                    elif file == "character_registry.py":
                        self.create_character_registry_file(file_path)
                    elif file == "__init__.py":
                        self.create_character_init_file(file_path)
                    
                    self.updates_applied.append(file)
                else:
                    print(f"✅ {file} exists")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating character definitions: {e}")
            self.errors.append(f"character_definitions: {e}")
            return False
    
    def create_character_spec_file(self, file_path: Path):
        """Create character_spec.py file."""
        content = '''from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class CharacterSpec:
    """Character specification for training data generation."""
    id: str
    name: str
    system_prompt: str
    traits: List[str]
    key_facts: List[str] = None
    
    def __post_init__(self):
        if self.key_facts is None:
            self.key_facts = []
'''
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Created {file_path}")
    
    def create_character_registry_file(self, file_path: Path):
        """Create character_registry.py file."""
        content = '''import json
from pathlib import Path
from typing import Dict, Any
from .character_spec import CharacterSpec

class CharacterRegistry:
    """Registry for managing character definitions."""
    
    def __init__(self, characters_file: str = "characters.json"):
        self.characters_file = Path(characters_file)
        self.characters = self.load_characters()
    
    def load_characters(self) -> Dict[str, Any]:
        """Load characters from JSON file."""
        if not self.characters_file.exists():
            return {}
        
        with open(self.characters_file, 'r') as f:
            return json.load(f)
    
    def get_character(self, character_id: str) -> CharacterSpec:
        """Get character specification by ID."""
        if character_id not in self.characters:
            raise ValueError(f"Character {character_id} not found")
        
        char_data = self.characters[character_id]
        return CharacterSpec(
            id=character_id,
            name=char_data.get("name", character_id),
            system_prompt=char_data.get("system_prompt", ""),
            traits=char_data.get("traits", []),
            key_facts=char_data.get("key_facts", [])
        )
    
    def list_characters(self) -> List[str]:
        """List all available character IDs."""
        return list(self.characters.keys())
'''
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Created {file_path}")
    
    def create_character_init_file(self, file_path: Path):
        """Create __init__.py file."""
        content = '''from .character_spec import CharacterSpec
from .character_registry import CharacterRegistry

__all__ = ["CharacterSpec", "CharacterRegistry"]
'''
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Created {file_path}")
    
    def update_shared_components(self) -> bool:
        """Update shared components."""
        print("📝 Updating shared components...")
        
        try:
            shared_path = self.clean_folder_path / "shared"
            required_files = ["api_client.py", "models.py", "config.py", "__init__.py"]
            
            for file in required_files:
                file_path = shared_path / file
                if not file_path.exists():
                    print(f"⚠️  {file} missing - creating basic version")
                    self.create_shared_file(file_path, file)
                    self.updates_applied.append(file)
                else:
                    print(f"✅ {file} exists")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating shared components: {e}")
            self.errors.append(f"shared_components: {e}")
            return False
    
    def create_shared_file(self, file_path: Path, file_name: str):
        """Create shared component file."""
        if file_name == "api_client.py":
            content = '''import openai
from typing import Dict, Any, Optional

class APIClient:
    """API client for LLM services."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
    
    async def call_llm_api(self, messages: List[Dict], model: str, **kwargs) -> Dict[str, Any]:
        """Call LLM API with messages."""
        # Implementation here
        pass
'''
        elif file_name == "models.py":
            content = '''from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Chat:
    """Chat conversation model."""
    messages: List[Dict[str, str]]
    character_id: str

@dataclass
class GenerationConfig:
    """Configuration for data generation."""
    num_chats: int = 20
    max_turns: int = 5
    temperature: float = 0.7
    model: str = "gpt-3.5-turbo"
    basic_question_percentage: float = 0.4
'''
        elif file_name == "config.py":
            content = '''import os
from typing import Dict, Any

class Config:
    """Configuration management."""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
    
    def get_api_key(self, service: str) -> str:
        """Get API key for service."""
        return getattr(self, f"{service}_api_key", None)
'''
        elif file_name == "__init__.py":
            content = '''from .api_client import APIClient
from .models import Chat, GenerationConfig
from .config import Config

__all__ = ["APIClient", "Chat", "GenerationConfig", "Config"]
'''
        
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Created {file_path}")
    
    def run_verification_tests(self) -> bool:
        """Run verification tests after updates."""
        print("🧪 Running verification tests...")
        
        try:
            # Test imports
            sys.path.append(str(self.clean_folder_path))
            
            # Test character definition imports
            from character_definition import CharacterSpec
            print("✅ Character definition imports work")
            
            # Test data generation imports
            from data_generation.chat_generation import generate_basic_chats
            print("✅ Data generation imports work")
            
            # Test SFT training imports
            from data_generation.train_sft_models import convert_to_openai_format
            print("✅ SFT training imports work")
            
            # Test shared component imports
            from shared.api_client import APIClient
            from shared.models import Chat
            print("✅ Shared component imports work")
            
            return True
            
        except Exception as e:
            print(f"❌ Verification tests failed: {e}")
            self.errors.append(f"verification: {e}")
            return False
    
    def generate_update_report(self) -> str:
        """Generate update report."""
        report = f"""
# Clean Folder Update Report

## Updates Applied

"""
        
        for update in self.updates_applied:
            report += f"- ✅ {update}\n"
        
        if self.errors:
            report += "\n## Errors\n\n"
            for error in self.errors:
                report += f"- ❌ {error}\n"
        
        report += f"""
## Summary

- **Updates Applied**: {len(self.updates_applied)}
- **Errors**: {len(self.errors)}
- **Status**: {'✅ Success' if not self.errors else '⚠️  Partial Success'}

## Next Steps

1. Run verification tests to confirm everything works
2. Test the complete pipeline end-to-end
3. Run integration tests for all components
"""
        
        report_path = self.clean_folder_path / "UPDATE_REPORT.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"✅ Update report saved: {report_path}")
        return str(report_path)
    
    def run_complete_update(self) -> Dict[str, Any]:
        """Run complete update process."""
        print("🚀 Starting complete clean_folder update...")
        print("=" * 60)
        
        # Update all components
        updates = {
            "data_generation": self.update_data_generation(),
            "character_definitions": self.update_character_definitions(),
            "shared_components": self.update_shared_components()
        }
        
        # Run verification tests
        verification_success = self.run_verification_tests()
        
        # Generate report
        report_path = self.generate_update_report()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Update Summary:")
        print("=" * 60)
        
        for component, success in updates.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"   {component}: {status}")
        
        print(f"   Verification: {'✅ SUCCESS' if verification_success else '❌ FAILED'}")
        print(f"   Updates Applied: {len(self.updates_applied)}")
        print(f"   Errors: {len(self.errors)}")
        
        if all(updates.values()) and verification_success:
            print("\n🎉 All components updated successfully!")
        else:
            print("\n⚠️  Some components had issues. Check the update report.")
        
        return {
            "updates": updates,
            "verification_success": verification_success,
            "updates_applied": self.updates_applied,
            "errors": self.errors,
            "report_path": report_path
        }

def main():
    """Main update function."""
    clean_folder_path = "/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/clean_folder"
    
    updater = CleanFolderUpdater(clean_folder_path)
    results = updater.run_complete_update()
    
    print(f"\n📊 Check the update report: {results['report_path']}")
    
    return results

if __name__ == "__main__":
    main()
