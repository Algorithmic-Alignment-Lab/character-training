import os
import sys
import json
from typing import Dict, Any, List

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from conversations_ui.llm_api import call_llm_api

class TraitAdherenceEvaluator(BaseEvaluator):
    """
    Evaluates how well the assistant's responses adhere to the defined character traits.
    """
    async def evaluate(self, conversation_log: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses a judge model to evaluate trait adherence for each assistant turn.

        Args:
            conversation_log: A dictionary containing the character profile and conversation history.

        Returns:
            A dictionary containing the evaluation results for trait adherence.
        """
        character_profile = conversation_log.get("character_profile", {})
        traits = character_profile.get("traits", [])
        
        if not traits:
            return {"trait_adherence": {"error": "No traits found in character profile."}}

        conversation_history = conversation_log.get("conversation", [])
        assistant_responses = [msg["content"] for msg in conversation_history if msg["role"] == "assistant"]

        if not assistant_responses:
            return {"trait_adherence": {"error": "No assistant responses found in conversation."}}

        # Create a formatted transcript for the judge
        transcript = "\n".join([f'{msg["role"]}: {msg["content"]}' for msg in conversation_history])
        
        # Create the prompt for the judge model
        judge_prompt = f"""
        You are an expert evaluator assessing an AI assistant's adherence to a character persona.
        
        **Character Profile:**
        - Archetype: {character_profile.get('archetype', 'N/A')}
        - Defined Traits: {', '.join(traits)}

        **Conversation Transcript:**
        ---
        {transcript}
        ---

        **Instructions:**
        For each of the defined traits, please provide a score from 1 to 7 (1=Not at all, 7=Perfectly) on how well the assistant's collective responses embodied that trait. Provide a brief reasoning for each score.

        Please format your response as a JSON object with a single key "trait_scores", which is a list of objects, where each object has "trait", "score", and "reasoning".
        Example:
        {{
          "trait_scores": [
            {{
              "trait": "curiosity",
              "score": 6,
              "reasoning": "The assistant asked several follow-up questions that showed genuine interest."
            }}
          ]
        }}
        """

        messages = [{"role": "user", "content": judge_prompt}]
        
        # Call the judge model
        response = await call_llm_api(messages=messages, model=self.judge_model)

        # Parse the response
        try:
            # The response might be a string containing JSON
            if isinstance(response, str):
                # A simple clean to handle markdown code blocks if the LLM adds them
                if response.strip().startswith("```json"):
                    response = response.strip()[7:-3]
                result = json.loads(response)
            else:
                result = response # Or it might be an already parsed dict/pydantic model

            return {"trait_adherence": result}
        except (json.JSONDecodeError, TypeError) as e:
            return {"trait_adherence": {"error": "Failed to parse judge model response.", "raw_response": str(response)}}

