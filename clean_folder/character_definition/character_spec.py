"""
Character specification classes and validation.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from shared.models import CharacterSpec as BaseCharacterSpec

class CharacterSpec(BaseCharacterSpec):
    """Extended character specification with additional methods."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character spec to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "system_prompt": self.system_prompt,
            "traits": self.traits,
            "key_facts": self.key_facts,
            "backstory": self.backstory,
            "evaluation_configs": self.evaluation_configs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterSpec':
        """Create character spec from dictionary."""
        return cls(**data)
    
    def get_display_name(self) -> str:
        """Get display name for the character."""
        return f"{self.name} ({self.version})"
    
    def get_trait_summary(self) -> str:
        """Get a summary of character traits."""
        if not self.traits:
            return "No traits defined"
        return "; ".join(self.traits[:3]) + ("..." if len(self.traits) > 3 else "")
    
    def validate_consistency(self) -> List[str]:
        """Validate character specification for consistency."""
        issues = []
        
        # Check if system prompt mentions traits
        if self.traits:
            for trait in self.traits:
                if trait.lower() not in self.system_prompt.lower():
                    issues.append(f"Trait '{trait}' not mentioned in system prompt")
        
        # Check if key facts are mentioned in system prompt or backstory
        if self.key_facts:
            combined_text = (self.system_prompt + " " + (self.backstory or "")).lower()
            for fact in self.key_facts:
                if fact.lower() not in combined_text:
                    issues.append(f"Key fact '{fact}' not mentioned in system prompt or backstory")
        
        # Check for reasonable length
        if len(self.system_prompt) < 50:
            issues.append("System prompt is very short (less than 50 characters)")
        
        if len(self.system_prompt) > 2000:
            issues.append("System prompt is very long (more than 2000 characters)")
        
        return issues
