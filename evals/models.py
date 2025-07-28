"""
Pydantic models for validating conversation generation and evaluation data.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class APICallLog(BaseModel):
    """Logs a single API call to an LLM."""
    model: str
    messages: List[Dict[str, str]]
    raw_response: Union[Dict[str, Any], str]
    thinking_content: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ConversationMessage(BaseModel):
    """A single message in a conversation."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    api_call_log: Optional[APICallLog] = None


class GeneratedConversation(BaseModel):
    """A complete conversation between two personas."""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_log: List[ConversationMessage]
    initial_context: str = Field(..., min_length=1)
    
    @field_validator('conversation_log')
    @classmethod
    def validate_conversation_log(cls, v):
        if len(v) < 2:
            raise ValueError("Conversation must have at least 2 messages")
        
        # Check alternating roles starting with user
        expected_role = "user"
        for i, msg in enumerate(v):
            if msg.role != expected_role:
                raise ValueError(f"Message {i} should be '{expected_role}', got '{msg.role}'")
            expected_role = "assistant" if expected_role == "user" else "user"
        
        return v


class ConversationGenerationMetadata(BaseModel):
    """Metadata for a conversation generation session."""
    num_conversations: int = Field(..., gt=0)
    num_turns: int = Field(..., gt=0)
    user_persona: str
    assistant_persona: str
    assistant_model: str
    user_model: str
    topic: str
    output_file: Optional[str] = None
    input_file: Optional[str] = None
    total_conversations: int = Field(..., ge=0)
    generation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    
class ConversationDataset(BaseModel):
    """A complete dataset of conversations with metadata."""
    metadata: ConversationGenerationMetadata
    conversations: List[GeneratedConversation]
    
    @model_validator(mode='after')
    def validate_conversations_count(self):
        if len(self.conversations) != self.metadata.total_conversations:
            raise ValueError(f"Expected {self.metadata.total_conversations} conversations, got {len(self.conversations)}")
        return self


class EvaluationResult(BaseModel):
    """Result of evaluating a single conversation."""
    conversation_id: str
    evaluation_score: float = Field(..., ge=0.0, le=10.0)
    is_in_character: bool
    failure_type: Optional[str] = None
    analysis: str
    trait_scores: Dict[str, float] = Field(default_factory=dict)
    evaluation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @field_validator('trait_scores')
    @classmethod
    def validate_trait_scores(cls, v):
        for trait, score in v.items():
            if not 1.0 <= score <= 5.0:
                raise ValueError(f"Trait score for '{trait}' must be between 1.0 and 5.0, got {score}")
        return v


class EvaluationBatch(BaseModel):
    """A batch of evaluation results."""
    evaluations: List[EvaluationResult]
    batch_metadata: Dict[str, Any] = Field(default_factory=dict)
    total_evaluated: int = Field(..., ge=0)
    
    @model_validator(mode='after')
    @classmethod
    def validate_evaluations_count(cls, self):
        if len(self.evaluations) != self.total_evaluated:
            raise ValueError(f"Expected {self.total_evaluated} evaluations, got {len(self.evaluations)}")
        return self


class APICallResult(BaseModel):
    """Result of an API call with error handling."""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    model_used: str
    attempt_count: int = Field(..., ge=1)
    duration_seconds: Optional[float] = None
    
    @model_validator(mode='after')
    @classmethod
    def validate_result(cls, values):
        if values.get('success') and not values.get('content'):
            raise ValueError("Successful API call must have content")
        if not values.get('success') and not values.get('error'):
            raise ValueError("Failed API call must have error message")
        return values


class WorkerResult(BaseModel):
    """Result from a parallel worker."""
    worker_id: int
    task_id: str
    success: bool
    result: Optional[Union[GeneratedConversation, EvaluationResult]] = None
    error: Optional[str] = None
    duration_seconds: float
    
    @field_validator('result')
    @classmethod
    def validate_result_on_success(cls, v, info):
        if info.data.get('success') and v is None:
            raise ValueError("Successful worker result must have a result")
        return v


class ProgressStats(BaseModel):
    """Progress statistics for parallel processing."""
    total_tasks: int = Field(..., ge=0)
    completed_tasks: int = Field(..., ge=0)
    successful_tasks: int = Field(..., ge=0)
    failed_tasks: int = Field(..., ge=0)
    active_workers: int = Field(..., ge=0, le=100)  # Max 100 workers
    estimated_time_remaining_seconds: Optional[float] = None
    
    @field_validator('completed_tasks')
    @classmethod
    def validate_completed_tasks(cls, v, info):
        total = info.data.get('total_tasks', 0)
        if v > total:
            raise ValueError("Completed tasks cannot exceed total tasks")
        return v
    
    @field_validator('successful_tasks', 'failed_tasks')
    @classmethod
    def validate_task_counts(cls, v, info):
        completed = info.data.get('completed_tasks', 0)
        if v > completed:
            raise ValueError("Task count cannot exceed completed tasks")
        return v
    
    @model_validator(mode='after')
    def validate_task_totals(self):
        if self.successful_tasks + self.failed_tasks != self.completed_tasks:
            raise ValueError("Successful + failed tasks must equal completed tasks")
        return self


class LLMCallResult(BaseModel):
    """The result of a single LLM API call, including the log."""
    response_text: str
    structured_response: Optional[Any] = None
    api_log: APICallLog
    error: Optional[str] = None
