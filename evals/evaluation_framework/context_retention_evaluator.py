import os
import sys
from typing import Dict, Any, List
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from conversations_ui.llm_api import call_llm_api

class ContextRetentionResult(BaseModel):
    reasoning: str = Field(description="Detailed reasoning for the context retention score.")
    retention_score: int = Field(description="Score from 1-7 (1=Poor Retention, 7=Excellent Retention).")
    missed_context: List[str] = Field(default_factory=list, description="List of specific details the assistant forgot or ignored.")

class ContextRetentionEvaluator(BaseEvaluator):
    """
    Evaluates the character's ability to retain and use context from the conversation.
    """
    async def evaluate(self, conversation_log: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> dict:
        character_name = character_profile.get("name", "Character")
        
        transcript = "\n".join([f"{turn['speaker']}: {turn['message']}" for turn in conversation_log])

        prompt = f"""
        You are an expert evaluator assessing an AI assistant's context retention.
        Context retention means the character remembers and appropriately uses information provided by the user throughout the conversation.

        **Character Profile:**
        - Name: {character_name}

        **Conversation Transcript:**
        ---
        {transcript}
        ---

        **Instructions:**
        Analyze the assistant's ({character_name}'s) responses. Does the character remember key details from earlier in the conversation? Does it ignore or forget important user-provided information?
        
        On a scale of 1-7 (1=Poor Retention, 7=Excellent Retention), rate the character's context retention.
        Provide detailed reasoning for your score first, then the score, and a list of any specific details the assistant missed.
        
        Format your response as a JSON object that adheres to the following Pydantic model:
        ```pydantic
        class ContextRetentionResult(BaseModel):
            reasoning: str = Field(description="Detailed reasoning for the context retention score.")
            retention_score: int = Field(description="Score from 1-7 (1=Poor Retention, 7=Excellent Retention).")
            missed_context: List[str] = Field(default_factory=list, description="List of specific details the assistant forgot or ignored.")
        ```
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await call_llm_api(messages, self.judge_model, response_model=ContextRetentionResult)
            return response.model_dump()
        except Exception as e:
            return {"error": f"Failed to get valid JSON response: {e}"}

