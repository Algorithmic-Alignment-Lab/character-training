import os
import sys
import json
from typing import Dict, Any, List

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from conversations_ui.llm_api import call_llm_api

import os
import sys
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from conversations_ui.llm_api import call_llm_api

class TraitScore(BaseModel):
    trait: str = Field(description="The trait being evaluated.")
    reasoning: str = Field(description="Detailed reasoning for the score.")
    score: int = Field(description="Score from 1-7 (1=Not at all, 7=Perfectly).")

class TraitAdherenceResult(BaseModel):
    trait_scores: List[TraitScore]

class TraitAdherenceEvaluator(BaseEvaluator):
    """
    Evaluates how well the assistant's responses adhere to the defined character traits.
    """
    async def evaluate(self, conversation_log: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses a judge model to evaluate trait adherence for each assistant turn.
        """
        traits = character_profile.get("traits", [])
        character_name = character_profile.get("name", "Character")
        
        if not traits:
            return {"error": "No traits found in character profile."}

        transcript = "\n".join([f'{msg["speaker"]}: {msg["message"]}' for msg in conversation_log])
        
        judge_prompt = f"""
        You are an expert evaluator assessing an AI assistant's adherence to a character persona.
        
        **Character Profile:**
        - Name: {character_name}
        - Archetype: {character_profile.get('archetype', 'N/A')}
        - Defined Traits: {', '.join(traits)}
        - System Prompt: {character_profile.get('system_prompt', 'N/A')}

        **Conversation Transcript:**
        ---
        {transcript}
        ---

        **Instructions:**
        For each of the defined traits, provide detailed reasoning for your score first, then the score itself from 1 to 7 (1=Not at all, 7=Perfectly) on how well the assistant's collective responses embodied that trait. Your evaluation should be based *only* on the assistant's dialogue ({character_name}).

        Format your response as a JSON object that adheres to the following Pydantic model:
        ```pydantic
        class TraitScore(BaseModel):
            trait: str = Field(description="The trait being evaluated.")
            reasoning: str = Field(description="Detailed reasoning for the score.")
            score: int = Field(description="Score from 1-7 (1=Not at all, 7=Perfectly).")

        class TraitAdherenceResult(BaseModel):
            trait_scores: List[TraitScore]
        ```
        """

        messages = [{"role": "user", "content": judge_prompt}]
        
        try:
            response = await call_llm_api(messages, self.judge_model, response_format=TraitAdherenceResult)
            if isinstance(response, dict) and "error" in response:
                return response
            return response.model_dump()
        except Exception as e:
            return {"error": f"Failed to get valid JSON response: {e}"}


