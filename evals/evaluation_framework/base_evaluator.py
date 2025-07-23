from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseEvaluator(ABC):
    def __init__(self, judge_model):
        self.judge_model = judge_model

    @abstractmethod
    def evaluate(self, conversation_log: List[Dict[str, Any]], character_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a conversation log against specific criteria.

        Args:
            conversation_log (List[Dict[str, Any]]): The conversation to be evaluated.
            character_profile (Dict[str, Any]): The profile of the character being evaluated.

        Returns:
            A dictionary containing the evaluation results (e.g., score, reasoning).
        """
        pass
