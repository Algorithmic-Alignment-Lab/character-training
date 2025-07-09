from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EvaluationType(str, Enum):
    SINGLE = "single"
    ELO = "elo"


class Idea(BaseModel):
    id: str
    text: str
    created_at: datetime = Field(default_factory=datetime.now)
    round_generated: int
    selected: bool = False


class Context(BaseModel):
    id: str
    idea_id: str
    pages: int
    content: str
    created_at: datetime = Field(default_factory=datetime.now)


class ConversationConfig(BaseModel):
    model: str
    system_prompt: str
    user_message_template: str
    ideas_filepath: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    role: str
    content: str


class Conversation(BaseModel):
    id: str
    idea_id: str
    context_id: str
    config: ConversationConfig
    messages: List[Message]
    created_at: datetime = Field(default_factory=datetime.now)


class TraitJudgment(BaseModel):
    trait: str
    score: int = Field(ge=1, le=5)
    reasoning: str


class SingleJudgment(BaseModel):
    id: str
    conversation_id: str
    judge_model: str
    trait_judgments: List[TraitJudgment]
    overall_reasoning: str
    created_at: datetime = Field(default_factory=datetime.now)


class ConversationRanking(BaseModel):
    conversation_id: str
    rank: int
    score: float


class EloComparison(BaseModel):
    id: str
    conversation_ids: List[str]
    judge_model: str
    trait: str
    rankings: List[ConversationRanking]
    reasoning: str
    created_at: datetime = Field(default_factory=datetime.now)


class TraitSummary(BaseModel):
    trait: str
    average_score: float
    std_deviation: float
    score_distribution: Dict[str, int]


class EloSummary(BaseModel):
    trait: str
    elo_scores: List[float]
    rankings: List[int]


class EvaluationSummary(BaseModel):
    id: str
    filepath: str
    trait_summaries: List[TraitSummary] = []
    elo_summaries: List[EloSummary] = []
    overall_score: float
    created_at: datetime = Field(default_factory=datetime.now)


class EvaluationResults(BaseModel):
    id: str
    evaluation_type: EvaluationType
    filepaths: List[str]
    judge_model: str
    results: List[Any]
    summaries: List[EvaluationSummary]
    created_at: datetime = Field(default_factory=datetime.now)