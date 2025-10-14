"""
Chat generation for creating synthetic training data.
"""
import asyncio
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.api_client import APIClient
from shared.models import Chat, GenerationConfig, TrainingData
from character_definition import CharacterSpec

class ChatGenerator:
    """Generate synthetic chats for character training."""
    
    def __init__(self, character_spec: CharacterSpec, api_client: APIClient):
        self.character_spec = character_spec
        self.api_client = api_client
    
    async def generate_chats(self, config: GenerationConfig) -> List[Chat]:
        """Generate synthetic chats based on configuration."""
        print(f"🎭 Generating {config.num_chats} chats for character: {self.character_spec.name}")
        
        # Calculate basic vs character-specific chats
        basic_count = int(config.num_chats * config.basic_question_percentage)
        character_count = config.num_chats - basic_count
        
        chats = []
        
        # Generate basic question chats
        if basic_count > 0:
            print(f"📝 Generating {basic_count} basic question chats...")
            basic_chats = await self._generate_basic_chats(basic_count, config)
            chats.extend(basic_chats)
        
        # Generate character-specific chats
        if character_count > 0:
            print(f"🎭 Generating {character_count} character-specific chats...")
            character_chats = await self._generate_character_chats(character_count, config)
            chats.extend(character_chats)
        
        print(f"✅ Generated {len(chats)} total chats")
        return chats
    
    async def _generate_basic_chats(self, num_chats: int, config: GenerationConfig) -> List[Chat]:
        """Generate basic question-answer chats."""
        basic_questions = [
            "What is the capital of France?",
            "How do you calculate the area of a circle?",
            "What is photosynthesis?",
            "Explain the water cycle.",
            "What are the main causes of climate change?",
            "How does a computer work?",
            "What is the difference between weather and climate?",
            "Explain the concept of gravity.",
            "What is the periodic table?",
            "How do plants make their own food?"
        ]
        
        chats = []
        for i in range(num_chats):
            question = random.choice(basic_questions)
            messages = [
                {"role": "user", "content": question},
                {"role": "assistant", "content": await self._generate_response(question, config)}
            ]
            
            chat = Chat(
                messages=messages,
                character_id=self.character_spec.id
            )
            chats.append(chat)
        
        return chats
    
    async def _generate_character_chats(self, num_chats: int, config: GenerationConfig) -> List[Chat]:
        """Generate character-specific chats."""
        chats = []
        
        # Generate chats based on character traits
        for i in range(num_chats):
            # Create a scenario based on character traits
            scenario = self._create_character_scenario()
            messages = await self._generate_conversation(scenario, config)
            
            chat = Chat(
                messages=messages,
                character_id=self.character_spec.id
            )
            chats.append(chat)
        
        return chats
    
    def _create_character_scenario(self) -> Dict[str, Any]:
        """Create a scenario based on character traits."""
        scenarios = []
        
        # Create scenarios based on character traits
        for trait in self.character_spec.traits:
            if "helpful" in trait.lower():
                scenarios.append({
                    "type": "help_request",
                    "description": "User asks for help with a problem",
                    "trait": trait
                })
            elif "creative" in trait.lower():
                scenarios.append({
                    "type": "creative_task",
                    "description": "User requests creative assistance",
                    "trait": trait
                })
            elif "analytical" in trait.lower():
                scenarios.append({
                    "type": "analysis_request",
                    "description": "User needs analytical help",
                    "trait": trait
                })
            elif "collaborative" in trait.lower():
                scenarios.append({
                    "type": "collaboration",
                    "description": "User wants to collaborate on something",
                    "trait": trait
                })
        
        # Default scenario if no specific traits match
        if not scenarios:
            scenarios.append({
                "type": "general_conversation",
                "description": "General conversation with the character",
                "trait": "general"
            })
        
        return random.choice(scenarios)
    
    async def _generate_conversation(self, scenario: Dict[str, Any], config: GenerationConfig) -> List[Dict[str, str]]:
        """Generate a multi-turn conversation."""
        messages = []
        
        # Generate initial user message based on scenario
        user_message = await self._generate_user_message(scenario)
        messages.append({"role": "user", "content": user_message})
        
        # Generate conversation turns
        for turn in range(config.max_turns - 1):
            # Generate assistant response
            assistant_response = await self._generate_response(
                user_message, config, conversation_context=messages
            )
            messages.append({"role": "assistant", "content": assistant_response})
            
            # Generate follow-up user message
            if turn < config.max_turns - 2:  # Don't generate user message for last turn
                user_message = await self._generate_follow_up_message(
                    messages, scenario
                )
                messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def _generate_user_message(self, scenario: Dict[str, Any]) -> str:
        """Generate initial user message based on scenario."""
        prompt = f"""
        Generate a realistic user message for this scenario:
        Type: {scenario['type']}
        Description: {scenario['description']}
        Character trait: {scenario['trait']}
        
        The message should be natural and engaging. Keep it concise (1-2 sentences).
        """
        
        messages = [{"role": "user", "content": prompt}]
        result = await self.api_client.call_llm_api(
            messages=messages,
            model="openrouter/anthropic/claude-3.5-sonnet",
            temperature=0.8,
            max_tokens=100
        )
        
        return result.response_text.strip()
    
    async def _generate_follow_up_message(self, conversation: List[Dict[str, str]], scenario: Dict[str, Any]) -> str:
        """Generate a follow-up user message."""
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation[-4:]])
        
        prompt = f"""
        Based on this conversation, generate a natural follow-up user message:
        
        {conversation_text}
        
        The message should continue the conversation naturally and be relevant to the character trait: {scenario['trait']}
        Keep it concise (1-2 sentences).
        """
        
        messages = [{"role": "user", "content": prompt}]
        result = await self.api_client.call_llm_api(
            messages=messages,
            model="openrouter/anthropic/claude-3.5-sonnet",
            temperature=0.8,
            max_tokens=100
        )
        
        return result.response_text.strip()
    
    async def _generate_response(self, user_message: str, config: GenerationConfig, conversation_context: Optional[List[Dict[str, str]]] = None) -> str:
        """Generate assistant response."""
        messages = [{"role": "system", "content": self.character_spec.system_prompt}]
        
        if conversation_context:
            messages.extend(conversation_context)
        else:
            messages.append({"role": "user", "content": user_message})
        
        result = await self.api_client.call_llm_api(
            messages=messages,
            model=config.model,
            temperature=config.temperature,
            max_tokens=500
        )
        
        return result.response_text.strip()
    
    async def generate_with_dpo(self, config: GenerationConfig) -> 'DPOResult':
        """Generate chats with DPO (Direct Preference Optimization) pipeline."""
        from .dpo_pipeline import DPOPipeline
        
        # First generate base chats
        chats = await self.generate_chats(config)
        
        # Then run DPO pipeline
        dpo_pipeline = DPOPipeline(self.api_client)
        return await dpo_pipeline.generate_preferences(chats)
