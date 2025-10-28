"""
Character registry for managing character specifications.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
try:
    from .character_spec import CharacterSpec
except ImportError:
    from character_spec import CharacterSpec
try:
    from shared.utils import save_json, load_json, ensure_dir
except ImportError:
    # Fallback if shared.utils not available
    def save_json(data, path):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    def load_json(path):
        with open(path, 'r') as f:
            return json.load(f)
    def ensure_dir(path):
        Path(path).mkdir(parents=True, exist_ok=True)

class CharacterRegistry:
    """Registry for managing character specifications."""
    
    def __init__(self, registry_file: Optional[Path] = None):
        if isinstance(registry_file, str):
            self.registry_file = Path(registry_file)
        else:
            self.registry_file = registry_file or Path("./characters.json")
        self.characters: Dict[str, CharacterSpec] = {}
        if self.registry_file.exists():
            self._load_registry()
    
    def _load_registry(self):
        """Load character registry from file."""
        if self.registry_file.exists():
            try:
                data = load_json(self.registry_file)
                for char_id, char_data in data.items():
                    # Add the character ID to the data if it's missing
                    if 'id' not in char_data:
                        char_data['id'] = char_id
                    self.characters[char_id] = CharacterSpec.from_dict(char_data)
            except Exception as e:
                print(f"Warning: Could not load character registry: {e}")
                self.characters = {}
        else:
            self.characters = {}
    
    def _save_registry(self):
        """Save character registry to file."""
        ensure_dir(self.registry_file.parent)
        data = {char_id: char_spec.to_dict() for char_id, char_spec in self.characters.items()}
        save_json(data, self.registry_file)
    
    def register_character(self, character_spec: CharacterSpec) -> None:
        """Register a new character."""
        # Validate character spec
        issues = character_spec.validate_consistency()
        if issues:
            print(f"Warning: Character '{character_spec.id}' has consistency issues:")
            for issue in issues:
                print(f"  - {issue}")
        
        self.characters[character_spec.id] = character_spec
        self._save_registry()
        print(f"✅ Registered character: {character_spec.get_display_name()}")
    
    def get_character(self, character_id: str) -> Optional[CharacterSpec]:
        """Get character by ID."""
        return self.characters.get(character_id)
    
    def list_characters(self) -> List[str]:
        """List all character IDs."""
        return list(self.characters.keys())
    
    def list_character_details(self) -> List[Dict[str, str]]:
        """List all characters with details."""
        return [
            {
                "id": char_id,
                "name": char_spec.name,
                "version": char_spec.version,
                "display_name": char_spec.get_display_name(),
                "trait_summary": char_spec.get_trait_summary()
            }
            for char_id, char_spec in self.characters.items()
        ]
    
    def validate_character(self, character_spec: CharacterSpec) -> bool:
        """Validate character specification."""
        try:
            # Check if character spec is valid
            issues = character_spec.validate_consistency()
            return len(issues) == 0
        except Exception:
            return False
    
    def update_character(self, character_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing character."""
        if character_id not in self.characters:
            print(f"Error: Character '{character_id}' not found")
            return False
        
        try:
            current_spec = self.characters[character_id]
            updated_data = current_spec.to_dict()
            updated_data.update(updates)
            
            updated_spec = CharacterSpec.from_dict(updated_data)
            self.characters[character_id] = updated_spec
            self._save_registry()
            print(f"✅ Updated character: {updated_spec.get_display_name()}")
            return True
        except Exception as e:
            print(f"Error updating character '{character_id}': {e}")
            return False
    
    def delete_character(self, character_id: str) -> bool:
        """Delete a character."""
        if character_id not in self.characters:
            print(f"Error: Character '{character_id}' not found")
            return False
        
        deleted_spec = self.characters.pop(character_id)
        self._save_registry()
        print(f"✅ Deleted character: {deleted_spec.get_display_name()}")
        return True
    
    def search_characters(self, query: str) -> List[CharacterSpec]:
        """Search characters by name, traits, or content."""
        query_lower = query.lower()
        results = []
        
        for char_spec in self.characters.values():
            # Search in name
            if query_lower in char_spec.name.lower():
                results.append(char_spec)
                continue
            
            # Search in traits
            for trait in char_spec.traits:
                if query_lower in trait.lower():
                    results.append(char_spec)
                    break
            
            # Search in system prompt
            if query_lower in char_spec.system_prompt.lower():
                results.append(char_spec)
                continue
        
        return results
    
    def export_character(self, character_id: str, export_path: Path) -> bool:
        """Export a single character to a file."""
        if character_id not in self.characters:
            print(f"Error: Character '{character_id}' not found")
            return False
        
        try:
            char_spec = self.characters[character_id]
            save_json(char_spec.to_dict(), export_path)
            print(f"✅ Exported character to: {export_path}")
            return True
        except Exception as e:
            print(f"Error exporting character: {e}")
            return False
    
    def import_character(self, import_path: Path) -> bool:
        """Import a character from a file."""
        try:
            char_data = load_json(import_path)
            char_spec = CharacterSpec.from_dict(char_data)
            self.register_character(char_spec)
            return True
        except Exception as e:
            print(f"Error importing character: {e}")
            return False
