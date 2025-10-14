"""
Simple character evaluator for open source release.
"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from shared.api_client import APIClient
from shared.models import CharacterSpec

@dataclass
class EvaluationResult:
    """Result of a single evaluation metric."""
    metric_name: str
    score: float  # 1-10 scale
    reasoning: str
    raw_response: str = ""

@dataclass
class ConversationEvaluation:
    """Complete evaluation results for a conversation."""
    conversation_id: str
    character_id: str
    individual_scores: List[EvaluationResult]
    overall_score: float
    evaluation_timestamp: str

class SimpleEvaluator:
    """Simple character evaluator using LLM judges."""
    
    def __init__(self, judge_model: str = "openrouter/anthropic/claude-3.5-sonnet", api_client: Optional[APIClient] = None):
        self.judge_model = judge_model
        self.api_client = api_client or APIClient()
    
    async def evaluate_conversation(
        self, 
        messages: List[Dict[str, str]], 
        character_spec: CharacterSpec
    ) -> ConversationEvaluation:
        """
        Evaluate a conversation for character adherence.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            character_spec: Character specification to evaluate against
            
        Returns:
            ConversationEvaluation with scores and reasoning
        """
        conversation_id = f"conv_{hash(str(messages))}"
        
        # Extract assistant responses
        assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
        
        if not assistant_messages:
            return ConversationEvaluation(
                conversation_id=conversation_id,
                character_id=character_spec.id,
                individual_scores=[],
                overall_score=0.0,
                evaluation_timestamp=""
            )
        
        # Evaluate trait adherence
        trait_scores = []
        for i, msg in enumerate(assistant_messages):
            for trait in character_spec.traits:
                result = await self._evaluate_trait_adherence(
                    msg['content'], trait, character_spec.name, i
                )
                trait_scores.append(result)
        
        # Evaluate overall character consistency
        consistency_result = await self._evaluate_character_consistency(
            messages, character_spec
        )
        
        # Calculate overall score
        all_scores = [r.score for r in trait_scores] + [consistency_result.score]
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
        
        return ConversationEvaluation(
            conversation_id=conversation_id,
            character_id=character_spec.id,
            individual_scores=trait_scores + [consistency_result],
            overall_score=overall_score,
            evaluation_timestamp="2025-01-01T00:00:00Z"
        )
    
    async def _evaluate_trait_adherence(
        self, 
        response: str, 
        trait: str, 
        character_name: str,
        message_index: int
    ) -> EvaluationResult:
        """Evaluate how well a response demonstrates a specific trait."""
        
        prompt = f"""
        Evaluate how well this response demonstrates the trait "{trait}" for the character "{character_name}".

        Response: {response}

        Rate from 1-10 where:
        - 1-3: Poorly demonstrates the trait
        - 4-6: Moderately demonstrates the trait  
        - 7-10: Strongly demonstrates the trait

        Provide your score and brief reasoning.

        Format your response as:
        Score: [1-10]
        Reasoning: [brief explanation]
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            result = await self.api_client.call_llm_api(
                messages=messages,
                model=self.judge_model,
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse score and reasoning
            score, reasoning = self._parse_evaluation_response(result.response_text)
            
            return EvaluationResult(
                metric_name=f"trait_adherence_{trait[:20]}",
                score=score,
                reasoning=reasoning,
                raw_response=result.response_text
            )
            
        except Exception as e:
            return EvaluationResult(
                metric_name=f"trait_adherence_{trait[:20]}",
                score=0.0,
                reasoning=f"Evaluation failed: {e}",
                raw_response=""
            )
    
    async def _evaluate_character_consistency(
        self, 
        messages: List[Dict[str, str]], 
        character_spec: CharacterSpec
    ) -> EvaluationResult:
        """Evaluate overall character consistency."""
        
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        prompt = f"""
        Evaluate how consistently this conversation demonstrates the character "{character_spec.name}".

        Character traits: {', '.join(character_spec.traits)}

        Conversation:
        {conversation_text}

        Rate from 1-10 where:
        - 1-3: Inconsistent with character
        - 4-6: Moderately consistent with character
        - 7-10: Highly consistent with character

        Provide your score and brief reasoning.

        Format your response as:
        Score: [1-10]
        Reasoning: [brief explanation]
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            result = await self.api_client.call_llm_api(
                messages=messages,
                model=self.judge_model,
                temperature=0.1,
                max_tokens=200
            )
            
            score, reasoning = self._parse_evaluation_response(result.response_text)
            
            return EvaluationResult(
                metric_name="character_consistency",
                score=score,
                reasoning=reasoning,
                raw_response=result.response_text
            )
            
        except Exception as e:
            return EvaluationResult(
                metric_name="character_consistency",
                score=0.0,
                reasoning=f"Evaluation failed: {e}",
                raw_response=""
            )
    
    def _parse_evaluation_response(self, response: str) -> tuple[float, str]:
        """Parse score and reasoning from evaluation response."""
        try:
            lines = response.strip().split('\n')
            score = 5.0  # Default score
            reasoning = "No reasoning provided"
            
            for line in lines:
                if line.startswith('Score:'):
                    score_text = line.replace('Score:', '').strip()
                    # Extract number from score text
                    import re
                    score_match = re.search(r'(\d+(?:\.\d+)?)', score_text)
                    if score_match:
                        score = float(score_match.group(1))
                        score = max(1.0, min(10.0, score))  # Clamp to 1-10
                elif line.startswith('Reasoning:'):
                    reasoning = line.replace('Reasoning:', '').strip()
            
            return score, reasoning
            
        except Exception:
            return 5.0, "Failed to parse evaluation response"
    
    async def evaluate_character_batch(
        self, 
        conversations: List[List[Dict[str, str]]], 
        character_spec: CharacterSpec
    ) -> List[ConversationEvaluation]:
        """Evaluate multiple conversations for a character."""
        results = []
        
        for i, messages in enumerate(conversations):
            print(f"Evaluating conversation {i+1}/{len(conversations)}")
            result = await self.evaluate_conversation(messages, character_spec)
            results.append(result)
        
        return results
    
    def save_evaluation_results(
        self, 
        results: List[ConversationEvaluation], 
        output_path: Path
    ) -> None:
        """Save evaluation results to JSON file."""
        output_data = {
            "evaluation_summary": {
                "total_conversations": len(results),
                "average_score": sum(r.overall_score for r in results) / len(results) if results else 0.0,
                "character_id": results[0].character_id if results else "unknown"
            },
            "individual_results": [
                {
                    "conversation_id": r.conversation_id,
                    "overall_score": r.overall_score,
                    "individual_scores": [
                        {
                            "metric_name": s.metric_name,
                            "score": s.score,
                            "reasoning": s.reasoning
                        }
                        for s in r.individual_scores
                    ]
                }
                for r in results
            ]
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"📊 Evaluation results saved to: {output_path}")
    
    def generate_evaluation_summary(self, results: List[ConversationEvaluation]) -> Dict[str, Any]:
        """Generate summary statistics from evaluation results."""
        if not results:
            return {"error": "No results to summarize"}
        
        all_scores = [r.overall_score for r in results]
        
        # Calculate metric averages
        metric_averages = {}
        for result in results:
            for score in result.individual_scores:
                if score.metric_name not in metric_averages:
                    metric_averages[score.metric_name] = []
                metric_averages[score.metric_name].append(score.score)
        
        # Calculate averages
        for metric in metric_averages:
            metric_averages[metric] = sum(metric_averages[metric]) / len(metric_averages[metric])
        
        return {
            "total_conversations": len(results),
            "overall_average": sum(all_scores) / len(all_scores),
            "overall_min": min(all_scores),
            "overall_max": max(all_scores),
            "metric_averages": metric_averages,
            "character_id": results[0].character_id
        }
