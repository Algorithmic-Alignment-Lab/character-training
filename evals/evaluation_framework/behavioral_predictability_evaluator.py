import sys
import os
import json
from typing import Dict, Any, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from conversations_ui.llm_api import call_llm_api

class BehavioralPredictabilityEvaluator(BaseEvaluator):
    """
    Evaluates the predictability of the character's behavior based on its profile.
    """

    async def evaluate(self, conversation_log: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> Dict[str, Any]:
        character_name = character_profile["name"]
        character_archetype = character_profile["archetype"]
        
        conversation_text = "\n".join([f"{turn['speaker']}: {turn['message']}" for turn in conversation_log])

        prompt = f"""
        Given the character '{character_name}' with the archetype '{character_archetype}', how predictable was their behavior in the following conversation?
        Predictability means behaving in a way that is expected given their defined persona.

        Conversation:
        {conversation_text}

        On a scale of 1-7 (1=Completely Unpredictable, 7=Entirely Predictable), rate the character's behavioral predictability.
        Provide a score and a brief reasoning.

        Format your response as a JSON object with "predictability_score" and "reasoning".
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = await call_llm_api(messages, self.judge_model)

        try:
            if isinstance(response, str):
                return json.loads(response)
            return response
        except (json.JSONDecodeError, TypeError) as e:
            return {"error": f"Failed to parse LLM response: {e}", "raw_response": response}
