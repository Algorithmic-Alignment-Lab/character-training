import sys
import os
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from conversations_ui.llm_api import call_llm_api

class BehavioralPredictabilityResult(BaseModel):
    reasoning: str = Field(description="Detailed reasoning for the predictability score.")
    predictability_score: int = Field(description="Score from 1-7 (1=Completely Unpredictable, 7=Entirely Predictable).")

class BehavioralPredictabilityEvaluator(BaseEvaluator):
    """
    Evaluates the predictability of the character's behavior based on its profile.
    """
    async def evaluate(self, conversation_log: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> Dict[str, Any]:
        character_name = character_profile.get("name", "Character")
        
        conversation_text = "\n".join([f"{turn['speaker']}: {turn['message']}" for turn in conversation_log])

        prompt = f"""
        You are an expert evaluator assessing an AI assistant's behavioral predictability.
        Predictability means behaving in a way that is expected given their defined persona.

        **Character Profile:**
        - Name: {character_name}
        - Archetype: {character_profile.get('archetype', 'N/A')}
        - System Prompt: {character_profile.get('system_prompt', 'N/A')}

        **Conversation Transcript:**
        ---
        {conversation_text}
        ---

        **Instructions:**
        On a scale of 1-7 (1=Completely Unpredictable, 7=Entirely Predictable), rate the character's behavioral predictability.
        Provide detailed reasoning for your score first, then the score itself.

        Format your response as a JSON object that adheres to the following Pydantic model:
        ```pydantic
        class BehavioralPredictabilityResult(BaseModel):
            reasoning: str = Field(description="Detailed reasoning for the predictability score.")
            predictability_score: int = Field(description="Score from 1-7 (1=Completely Unpredictable, 7=Entirely Predictable).")
        ```
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await call_llm_api(messages, self.judge_model, response_model=BehavioralPredictabilityResult)
            return response.model_dump()
        except Exception as e:
            return {"error": f"Failed to get valid JSON response: {e}"}

