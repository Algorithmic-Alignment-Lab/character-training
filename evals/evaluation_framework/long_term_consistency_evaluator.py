import os
import sys
from typing import Dict, Any, List
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from conversations_ui.llm_api import call_llm_api

class LongTermConsistencyResult(BaseModel):
    reasoning: str = Field(description="Detailed reasoning for the consistency score.")
    consistency_score: int = Field(description="Score from 1-7 (1=Very Inconsistent, 7=Very Consistent).")
    contradictions: List[str] = Field(default_factory=list, description="List of any contradictions found.")

class LongTermConsistencyEvaluator(BaseEvaluator):
    """
    Evaluates the character's consistency over a long conversation.
    """
    async def evaluate(self, conversation_log: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> dict:
        character_name = character_profile.get("name", "Character")
        
        transcript = "\n".join([f"{turn['speaker']}: {turn['message']}" for turn in conversation_log])

        prompt = f"""
        You are an expert evaluator assessing an AI assistant's long-term consistency.
        Long-term consistency means the character does not contradict itself or forget key details established earlier in the conversation.

        **Character Profile:**
        - Name: {character_name}
        - Archetype: {character_profile.get('archetype', 'N/A')}

        **Conversation Transcript:**
        ---
        {transcript}
        ---

        **Instructions:**
        Analyze the assistant's ({character_name}'s) responses throughout the entire conversation. Does the character maintain a consistent personality and memory? Note any contradictions or instances of forgetting.
        
        On a scale of 1-7 (1=Very Inconsistent, 7=Very Consistent), rate the character's long-term consistency.
        Provide detailed reasoning for your score first, then the score, and a list of any contradictions found.
        
        Format your response as a JSON object that adheres to the following Pydantic model:
        ```pydantic
        class LongTermConsistencyResult(BaseModel):
            reasoning: str = Field(description="Detailed reasoning for the consistency score.")
            consistency_score: int = Field(description="Score from 1-7 (1=Very Inconsistent, 7=Very Consistent).")
            contradictions: List[str] = Field(default_factory=list, description="List of any contradictions found.")
        ```
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await call_llm_api(messages, self.judge_model, response_format=LongTermConsistencyResult)
            if isinstance(response, dict) and "error" in response:
                return response
            return response.model_dump()
        except Exception as e:
            return {"error": f"Failed to get valid JSON response: {e}"}

