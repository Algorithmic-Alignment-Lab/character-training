import os
import sys
from typing import Dict, Any, List
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from evals.llm_api import call_llm_api_with_structured_response

class EngagementQualityResult(BaseModel):
    reasoning: str = Field(description="Detailed reasoning for the engagement score.")
    engagement_score: int = Field(description="Score from 1-7 (1=Very Unengaging, 7=Very Engaging).")

class EngagementQualityEvaluator(BaseEvaluator):
    """
    Evaluates the quality of engagement in the conversation.
    """
    async def evaluate(self, conversation_log: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> dict:
        character_name = character_profile.get("name", "Character")
        
        transcript = "\n".join([f"{turn['speaker']}: {turn['message']}" for turn in conversation_log])

        prompt = f"""
        You are an expert evaluator assessing an AI assistant's engagement quality.
        Engagement quality refers to how interesting, natural, and compelling the conversation is.

        **Character Profile:**
        - Name: {character_name}
        - Archetype: {character_profile.get('archetype', 'N/A')}

        **Conversation Transcript:**
        ---
        {transcript}
        ---

        **Instructions:**
        Analyze the entire conversation. How engaging was the interaction? Did the assistant's responses contribute positively to the flow and interest of the dialogue?
        
        On a scale of 1-7 (1=Very Unengaging, 7=Very Engaging), rate the overall engagement quality.
        Provide detailed reasoning for your score first, then the score itself.
        
        Format your response as a JSON object that adheres to the following Pydantic model:
        ```pydantic
        class EngagementQualityResult(BaseModel):
            reasoning: str = Field(description="Detailed reasoning for the engagement score.")
            engagement_score: int = Field(description="Score from 1-7 (1=Very Unengaging, 7=Very Engaging).")
        ```
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await call_llm_api_with_structured_response(messages, self.judge_model, EngagementQualityResult)
            if isinstance(response, dict) and "error" in response:
                return response
            return response.model_dump()
        except Exception as e:
            return {"error": f"Failed to get valid JSON response: {e}"}

