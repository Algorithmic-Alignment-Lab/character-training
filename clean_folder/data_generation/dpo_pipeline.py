"""
DPO (Direct Preference Optimization) pipeline for generating preference data.
"""
import asyncio
import random
from typing import List, Dict, Any, Tuple
from shared.api_client import APIClient
from shared.models import Chat, DPOResult, RankingResult

class DPOPipeline:
    """DPO pipeline for generating preference data."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    async def generate_preferences(self, chats: List[Chat]) -> DPOResult:
        """Generate preference data from chats."""
        print(f"🔄 Generating DPO preferences for {len(chats)} chats...")
        
        preferred_chats = []
        rejected_chats = []
        
        for chat in chats:
            try:
                # Generate two responses and rank them
                responses = await self._generate_multiple_responses(chat)
                if len(responses) >= 2:
                    ranked = await self._rank_responses(responses, chat)
                    preferred_chats.append(ranked[0])
                    rejected_chats.append(ranked[1])
            except Exception as e:
                print(f"Warning: Failed to generate preferences for chat: {e}")
                continue
        
        success_rate = len(preferred_chats) / len(chats) if chats else 0.0
        
        return DPOResult(
            preferred_chats=preferred_chats,
            rejected_chats=rejected_chats,
            total_pairs=len(preferred_chats),
            success_rate=success_rate
        )
    
    async def _generate_multiple_responses(self, chat: Chat) -> List[Chat]:
        """Generate multiple responses for the same chat."""
        responses = []
        
        # Generate 2-3 different responses
        for i in range(3):
            try:
                # Create a new chat with the same user message but different assistant response
                user_message = chat.messages[0]["content"]
                
                # Generate response with different temperature
                temperature = 0.7 + (i * 0.3)  # 0.7, 1.0, 1.3
                
                response = await self._generate_single_response(user_message, temperature)
                
                new_chat = Chat(
                    messages=[
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": response}
                    ],
                    character_id=chat.character_id
                )
                responses.append(new_chat)
                
            except Exception as e:
                print(f"Warning: Failed to generate response {i}: {e}")
                continue
        
        return responses
    
    async def _generate_single_response(self, user_message: str, temperature: float) -> str:
        """Generate a single response to a user message."""
        messages = [
            {"role": "user", "content": user_message}
        ]
        
        result = await self.api_client.call_llm_api(
            messages=messages,
            model="gpt-4o",
            temperature=temperature,
            max_tokens=200
        )
        
        return result.response_text.strip()
    
    async def _rank_responses(self, responses: List[Chat], original_chat: Chat) -> List[Chat]:
        """Rank responses by quality."""
        if len(responses) < 2:
            return responses
        
        # Simple ranking based on response length and quality heuristics
        # In a real implementation, you'd use a judge model
        ranked = sorted(responses, key=lambda x: self._score_response(x), reverse=True)
        return ranked
    
    def _score_response(self, chat: Chat) -> float:
        """Score a response based on heuristics."""
        if not chat.messages:
            return 0.0
        
        response = chat.messages[-1]["content"]
        
        # Simple scoring based on length and content quality
        score = 0.0
        
        # Length score (prefer moderate length)
        length = len(response)
        if 50 <= length <= 300:
            score += 1.0
        elif length < 50:
            score += 0.5
        else:
            score += 0.8
        
        # Content quality heuristics
        if response.endswith("?"):
            score += 0.2  # Prefer responses that end with questions
        
        if "help" in response.lower():
            score += 0.1  # Prefer helpful responses
        
        return score
    
    async def multi_response_ranking(self, chats: List[Chat], num_responses: int = 3) -> RankingResult:
        """Generate multiple responses and rank them."""
        print(f"🔄 Generating {num_responses} responses per chat for {len(chats)} chats...")
        
        all_rankings = []
        
        for chat in chats:
            try:
                responses = await self._generate_multiple_responses(chat)
                if len(responses) >= num_responses:
                    ranked = await self._rank_responses(responses[:num_responses], chat)
                    all_rankings.extend(ranked)
            except Exception as e:
                print(f"Warning: Failed to rank responses for chat: {e}")
                continue
        
        if not all_rankings:
            return RankingResult(
                ranked_responses=[],
                ranking_scores=[],
                best_response={},
                worst_response={},
                ranking_timestamp=""
            )
        
        # Score all responses
        scores = [self._score_response(chat) for chat in all_rankings]
        
        # Find best and worst
        best_idx = scores.index(max(scores))
        worst_idx = scores.index(min(scores))
        
        return RankingResult(
            ranked_responses=[chat.to_dict() for chat in all_rankings],
            ranking_scores=scores,
            best_response=all_rankings[best_idx].to_dict(),
            worst_response=all_rankings[worst_idx].to_dict()
        )
