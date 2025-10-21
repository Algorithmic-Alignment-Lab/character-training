"""
Character specification classes and validation.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

class CharacterSpec(BaseModel):
    """Character specification for training and evaluation."""
    id: str
    name: str
    version: str
    system_prompt: str
    traits: List[str] = Field(default_factory=list)
    key_facts: List[str] = Field(default_factory=list)
    backstory: Optional[str] = None
    evaluations: List[str] = Field(default_factory=list)
    evaluation_configs: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('system_prompt')
    @classmethod
    def validate_system_prompt(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("System prompt must be at least 10 characters long")
        return v.strip()
    
    @field_validator('traits')
    @classmethod
    def validate_traits(cls, v):
        if not v:
            raise ValueError("Character must have at least one trait")
        return [trait.strip() for trait in v if trait.strip()]
    
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
            "evaluations": self.evaluations,
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