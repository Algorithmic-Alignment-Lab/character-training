#!/usr/bin/env python3
"""
Character validation system for checking character definitions, behaviors, and examples.
Provides detailed feedback on any issues found.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add current directory to path for imports
sys.path.append('.')

try:
    from character_registry import CharacterRegistry
    from character_spec import CharacterSpec
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the character_definition directory")
    sys.exit(1)

class CharacterValidator:
    """Validates character definitions, behaviors, and examples."""
    
    def __init__(self, characters_file: str = "characters.json", 
                 behaviors_file: str = "behaviors.json", 
                 examples_dir: str = "examples"):
        self.characters_file = characters_file
        self.behaviors_file = behaviors_file
        self.examples_dir = examples_dir
        self.issues = []
        self.warnings = []
        
    def validate_all(self, character_id: str = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all character components.
        
        Args:
            character_id: Specific character to validate, or None for all
            
        Returns:
            Tuple of (success, issues, warnings)
        """
        self.issues = []
        self.warnings = []
        
        print(f"🔍 Validating character system...")
        print("=" * 50)
        
        # Step 1: Validate character registry
        if not self._validate_character_registry():
            return False, self.issues, self.warnings
            
        # Step 2: Validate behaviors
        if not self._validate_behaviors():
            return False, self.issues, self.warnings
            
        # Step 3: Validate examples
        if not self._validate_examples():
            return False, self.issues, self.warnings
            
        # Step 4: Validate specific character if requested
        if character_id:
            if not self._validate_character(character_id):
                return False, self.issues, self.warnings
                
        # Step 5: Cross-validate character consistency
        if character_id:
            if not self._validate_character_consistency(character_id):
                return False, self.issues, self.warnings
                
        return len(self.issues) == 0, self.issues, self.warnings
    
    def _validate_character_registry(self) -> bool:
        """Validate character registry file and loading."""
        print("📋 Validating character registry...")
        
        # Check if characters file exists
        if not os.path.exists(self.characters_file):
            self.issues.append(f"Characters file not found: {self.characters_file}")
            return False
            
        # Try to load characters
        try:
            registry = CharacterRegistry(self.characters_file)
            print(f"✅ Character registry loaded successfully")
            print(f"   Found {len(registry.characters)} characters")
            
            # List all characters
            for char_id, char in registry.characters.items():
                print(f"   - {char_id}: {char.name}")
                
            return True
            
        except Exception as e:
            self.issues.append(f"Failed to load character registry: {e}")
            return False
    
    def _validate_behaviors(self) -> bool:
        """Validate behaviors file and format."""
        print("\n📋 Validating behaviors...")
        
        # Check if behaviors file exists
        if not os.path.exists(self.behaviors_file):
            self.issues.append(f"Behaviors file not found: {self.behaviors_file}")
            return False
            
        # Try to load behaviors
        try:
            with open(self.behaviors_file, 'r') as f:
                behaviors = json.load(f)
            print(f"✅ Behaviors file loaded successfully")
            print(f"   Found {len(behaviors)} behaviors")
            
            # Validate behavior format
            for behavior_id, description in behaviors.items():
                if not isinstance(description, str) or len(description.strip()) < 10:
                    self.issues.append(f"Invalid behavior format for '{behavior_id}': description too short")
                elif len(description.strip()) < 20:
                    self.warnings.append(f"Behavior '{behavior_id}' has very short description")
                    
            return True
            
        except json.JSONDecodeError as e:
            self.issues.append(f"Invalid JSON in behaviors file: {e}")
            return False
        except Exception as e:
            self.issues.append(f"Failed to load behaviors: {e}")
            return False
    
    def _validate_examples(self) -> bool:
        """Validate examples directory and files."""
        print("\n📋 Validating examples...")
        
        # Check if examples directory exists
        if not os.path.exists(self.examples_dir):
            self.issues.append(f"Examples directory not found: {self.examples_dir}")
            return False
            
        # Get all example files
        example_files = [f for f in os.listdir(self.examples_dir) if f.endswith('.json')]
        print(f"✅ Examples directory found")
        print(f"   Found {len(example_files)} example files")
        
        if len(example_files) == 0:
            self.warnings.append("No example files found in examples directory")
            return True
            
        # Validate each example file
        valid_examples = 0
        for example_file in example_files:
            if self._validate_example_file(os.path.join(self.examples_dir, example_file)):
                valid_examples += 1
                
        print(f"   {valid_examples}/{len(example_files)} example files are valid")
        
        if valid_examples == 0:
            self.issues.append("No valid example files found")
            return False
            
        return True
    
    def _validate_example_file(self, file_path: str) -> bool:
        """Validate a single example file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Check required fields
            required_fields = ['evaluator_model_id', 'target_model_id', 'target_system_prompt', 'events']
            for field in required_fields:
                if field not in data:
                    self.issues.append(f"Missing required field '{field}' in {os.path.basename(file_path)}")
                    return False
                    
            # Check events format
            events = data.get('events', [])
            if not isinstance(events, list) or len(events) == 0:
                self.issues.append(f"No events found in {os.path.basename(file_path)}")
                return False
                
            # Check event format
            for i, event in enumerate(events):
                if not isinstance(event, dict):
                    self.issues.append(f"Invalid event format at index {i} in {os.path.basename(file_path)}")
                    return False
                    
                required_event_fields = ['turn', 'event', 'content']
                for field in required_event_fields:
                    if field not in event:
                        self.issues.append(f"Missing field '{field}' in event {i} of {os.path.basename(file_path)}")
                        return False
                        
            return True
            
        except json.JSONDecodeError as e:
            self.issues.append(f"Invalid JSON in {os.path.basename(file_path)}: {e}")
            return False
        except Exception as e:
            self.issues.append(f"Error reading {os.path.basename(file_path)}: {e}")
            return False
    
    def _validate_character(self, character_id: str) -> bool:
        """Validate a specific character."""
        print(f"\n📋 Validating character '{character_id}'...")
        
        try:
            registry = CharacterRegistry(self.characters_file)
            character = registry.get_character(character_id)
            
            if character is None:
                self.issues.append(f"Character '{character_id}' not found")
                return False
                
            print(f"✅ Character '{character_id}' found: {character.name}")
            
            # Validate character fields
            if not character.system_prompt or len(character.system_prompt.strip()) < 10:
                self.issues.append(f"Character '{character_id}' has invalid system prompt")
                
            if not character.traits or len(character.traits) == 0:
                self.issues.append(f"Character '{character_id}' has no traits")
                
            if not character.evaluations or len(character.evaluations) == 0:
                self.issues.append(f"Character '{character_id}' has no evaluations")
                
            # Check for consistency issues
            consistency_issues = character.validate_consistency()
            if consistency_issues:
                for issue in consistency_issues:
                    self.warnings.append(f"Character '{character_id}' consistency issue: {issue}")
                    
            return True
            
        except Exception as e:
            self.issues.append(f"Error validating character '{character_id}': {e}")
            return False
    
    def _validate_character_consistency(self, character_id: str) -> bool:
        """Validate character consistency with behaviors and examples."""
        print(f"\n📋 Validating consistency for character '{character_id}'...")
        
        try:
            # Load character
            registry = CharacterRegistry(self.characters_file)
            character = registry.get_character(character_id)
            
            # Load behaviors
            with open(self.behaviors_file, 'r') as f:
                behaviors = json.load(f)
                
            # Check if all character evaluations have corresponding behaviors
            missing_behaviors = []
            for evaluation in character.evaluations:
                if evaluation not in behaviors:
                    missing_behaviors.append(evaluation)
                    
            if missing_behaviors:
                self.issues.append(f"Character '{character_id}' evaluations without behaviors: {missing_behaviors}")
                
            # Check if all character evaluations have corresponding examples
            missing_examples = []
            for evaluation in character.evaluations:
                example_file = os.path.join(self.examples_dir, f"{evaluation}.json")
                if not os.path.exists(example_file):
                    missing_examples.append(evaluation)
                    
            if missing_examples:
                self.issues.append(f"Character '{character_id}' evaluations without examples: {missing_examples}")
                
            # Check for orphaned behaviors (behaviors without characters)
            character_evaluations = set(character.evaluations)
            orphaned_behaviors = []
            for behavior_id in behaviors.keys():
                if behavior_id.startswith(f"{character_id}_") and behavior_id not in character_evaluations:
                    orphaned_behaviors.append(behavior_id)
                    
            if orphaned_behaviors:
                self.warnings.append(f"Orphaned behaviors for character '{character_id}': {orphaned_behaviors}")
                
            return True
            
        except Exception as e:
            self.issues.append(f"Error validating character consistency: {e}")
            return False
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        if len(self.issues) == 0:
            print("✅ All validations passed!")
        else:
            print(f"❌ {len(self.issues)} issues found:")
            for i, issue in enumerate(self.issues, 1):
                print(f"   {i}. {issue}")
                
        if len(self.warnings) > 0:
            print(f"\n⚠️  {len(self.warnings)} warnings:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
                
        print(f"\n🎯 Overall: {'PASS' if len(self.issues) == 0 else 'FAIL'}")


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate character definitions")
    parser.add_argument("--character", "-c", help="Specific character to validate")
    parser.add_argument("--characters-file", default="characters.json", help="Characters file path")
    parser.add_argument("--behaviors-file", default="behaviors.json", help="Behaviors file path")
    parser.add_argument("--examples-dir", default="examples", help="Examples directory path")
    
    args = parser.parse_args()
    
    validator = CharacterValidator(
        characters_file=args.characters_file,
        behaviors_file=args.behaviors_file,
        examples_dir=args.examples_dir
    )
    
    success, issues, warnings = validator.validate_all(args.character)
    validator.print_summary()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
