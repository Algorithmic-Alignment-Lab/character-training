"""
Pydantic models for the character training system.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

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

class Chat(BaseModel):
    """A single chat conversation."""
    messages: List[Dict[str, str]] = Field(..., min_length=2)
    character_id: str
    generation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        # Ensure alternating user/assistant roles starting with user
        expected_role = "user"
        for i, msg in enumerate(v):
            if msg.get('role') != expected_role:
                raise ValueError(f"Message {i} should be '{expected_role}', got '{msg.get('role')}'")
            expected_role = "assistant" if expected_role == "user" else "user"
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chat to dictionary."""
        return {
            "messages": self.messages,
            "character_id": self.character_id,
            "generation_timestamp": self.generation_timestamp
        }

class TrainingData(BaseModel):
    """Training data for fine-tuning."""
    chats: List[Chat]
    character_id: str
    total_examples: int
    generation_config: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def validate_chat_count(self):
        if len(self.chats) != self.total_examples:
            raise ValueError(f"Expected {self.total_examples} chats, got {len(self.chats)}")
        return self

class TrainingResult(BaseModel):
    """Result of a training operation."""
    model_id: str
    character_id: str
    training_data_path: str
    success: bool
    error: Optional[str] = None
    training_metrics: Dict[str, Any] = Field(default_factory=dict)
    training_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class DeploymentResult(BaseModel):
    """Result of a model deployment."""
    endpoint_id: str
    model_id: str
    deployment_url: str
    success: bool
    error: Optional[str] = None
    deployment_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class AuditResult(BaseModel):
    """Result of a character audit using Petri."""
    character_id: str
    special_instructions: List[str]
    transcript_paths: List[str]
    concern_scores: Dict[str, float]
    overall_concern_score: float
    concerning_behaviors: List[str]
    audit_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    model_configs: Dict[str, str]
    
    @field_validator('concern_scores')
    @classmethod
    def validate_concern_scores(cls, v):
        for instruction, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Concern score for '{instruction}' must be between 0.0 and 1.0, got {score}")
        return v

class EvaluationResult(BaseModel):
    """Result of character evaluation."""
    character_id: str
    evaluation_type: str
    scores: Dict[str, float]
    overall_score: float
    detailed_analysis: Dict[str, Any] = Field(default_factory=dict)
    transcript_paths: List[str] = Field(default_factory=list)
    evaluation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @field_validator('scores')
    @classmethod
    def validate_scores(cls, v):
        for metric, score in v.items():
            if not 0.0 <= score <= 10.0:
                raise ValueError(f"Score for '{metric}' must be between 0.0 and 10.0, got {score}")
        return v

class ComparisonResult(BaseModel):
    """Result of comparing multiple character versions."""
    character_ids: List[str]
    comparison_metrics: Dict[str, Dict[str, float]]
    best_character: str
    comparison_analysis: str
    comparison_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class GenerationConfig(BaseModel):
    """Configuration for data generation."""
    num_chats: int = Field(..., gt=0)
    max_turns: int = Field(default=10, gt=0)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    model: str
    enable_revision: bool = True
    enable_dpo: bool = True
    basic_question_percentage: float = Field(default=0.2, ge=0.0, le=1.0)

class DPOResult(BaseModel):
    """Result of DPO (Direct Preference Optimization) generation."""
    preferred_chats: List[Chat]
    rejected_chats: List[Chat]
    total_pairs: int
    success_rate: float
    generation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @model_validator(mode='after')
    def validate_pair_count(self):
        if len(self.preferred_chats) != len(self.rejected_chats):
            raise ValueError("Preferred and rejected chats must have the same count")
        if len(self.preferred_chats) != self.total_pairs:
            raise ValueError(f"Expected {self.total_pairs} pairs, got {len(self.preferred_chats)}")
        return self

class RankingResult(BaseModel):
    """Result of multi-response ranking."""
    ranked_responses: List[Dict[str, Any]]
    ranking_scores: List[float]
    best_response: Dict[str, Any]
    worst_response: Dict[str, Any]
    ranking_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
