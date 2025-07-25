import os
import sys
from typing import Dict, Any, List
from pydantic import BaseModel, Field

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from conversations_ui.llm_api import call_llm_api

class ReasoningAuthenticityResult(BaseModel):
    reasoning: str = Field(description="Detailed reasoning for the authenticity score.")
    authenticity_score: int = Field(description="Score from 1-7 (1=Very Inauthentic, 7=Very Authentic).")

class ReasoningAuthenticityEvaluator(BaseEvaluator):
    """
    Evaluates whether the character's reasoning is authentic and believable.
    """
    async def evaluate(self, conversation_log: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> Dict[str, Any]:
        character_name = character_profile.get("name", "Character")
        
        transcript = "\n".join([f"{turn['speaker']}: {turn['message']}" for turn in conversation_log])

        prompt = f"""
        You are an expert evaluator assessing an AI assistant's authenticity.
        Authenticity means the character's reasoning for its actions and statements feels genuine and consistent with its persona, not like a generic or evasive chatbot.

        **Character Profile:**
        - Name: {character_name}
        - Archetype: {character_profile.get('archetype', 'N/A')}
        - System Prompt: {character_profile.get('system_prompt', 'N/A')}

        **Conversation Transcript:**
        ---
        {transcript}
        ---

        **Instructions:**
        Analyze the assistant's ({character_name}'s) responses. Does its reasoning seem authentic and true to its defined character? Or does it feel like a generic AI providing canned answers?
        
        On a scale of 1-7 (1=Very Inauthentic, 7=Very Authentic), rate the character's reasoning authenticity.
        Provide detailed reasoning for your score first, then the score itself.
        
        Format your response as a JSON object that adheres to the following Pydantic model:
        ```pydantic
        class ReasoningAuthenticityResult(BaseModel):
            reasoning: str = Field(description="Detailed reasoning for the authenticity score.")
            authenticity_score: int = Field(description="Score from 1-7 (1=Very Inauthentic, 7=Very Authentic).")
        ```
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await call_llm_api(messages, self.judge_model, response_format=ReasoningAuthenticityResult)
            if isinstance(response, dict) and "error" in response:
                return response
            return response.model_dump()
        except Exception as e:
            return {"error": f"Failed to get valid JSON response: {e}"}

