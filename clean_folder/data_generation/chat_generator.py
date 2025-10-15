"""
Chat generation for creating synthetic training data.
"""
import asyncio
import random
import os
import json
import functools
import copy
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from shared.api_client import APIClient
from shared.models import Chat, GenerationConfig, TrainingData
from character_definition import CharacterSpec

class BatchConfig:
    """Configuration for batch processing."""
    def __init__(
        self,
        use_batch: bool = True,
        chunk_size: Optional[int] = None,
        use_cache: bool = False,
        batch_id_callback: Optional[Callable[[str], None]] = None,
        config_path: Optional[str] = None,
        character_id: Optional[str] = None
    ):
        self.use_batch = use_batch
        self.chunk_size = chunk_size
        self.use_cache = use_cache
        self.batch_id_callback = batch_id_callback
        self.config_path = config_path
        self.character_id = character_id

def _append_batch_id_to_config(config_path: str, batch_id: str, operation: str, character_id: Optional[str] = None):
    """Append batch ID to config file for tracking."""
    if not config_path:
        return
    
    try:
        config_data = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        
        if operation not in config_data:
            config_data[operation] = []
        
        batch_info = {
            "batch_id": batch_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "character_id": character_id
        }
        config_data[operation].append(batch_info)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save batch ID to config: {e}")

# Import batch processing dependencies
try:
    from safetytooling.apis import InferenceAPI
    from safetytooling.apis.batch_api import BatchInferenceAPI
    from safetytooling.data_models import ChatMessage, MessageRole, Prompt
    from safetytooling.utils import utils as safetytooling_utils
    BATCH_AVAILABLE = True
except ImportError:
    BATCH_AVAILABLE = False
    print("Warning: Batch processing dependencies not available. Falling back to regular API calls.")

# Setup batch APIs if available
if BATCH_AVAILABLE:
    safetytooling_utils.setup_environment(
        logging_level="warning",
        openai_tag="OPENAI_API_KEY",
        anthropic_tag="ANTHROPIC_API_KEY",
    )
    BATCH_API = BatchInferenceAPI(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY_BATCH"))
    API = InferenceAPI(anthropic_num_threads=20)

async def batch_generate(
    api: InferenceAPI = None,
    batch_api: BatchInferenceAPI = None,
    use_batch_api: bool = True,
    prompts: list[Prompt] | Prompt = None,
    model_id: str = None,
    use_tqdm: bool = True,
    n: int = 1,
    use_cache: bool | None = None,
    chunk_size: int | None = None,
    batch_id_callback: Callable[[str], None] | None = None,
    **kwargs,
) -> list[Any]:
    """Batch generation function similar to finetuning_data_generation."""
    if not BATCH_AVAILABLE:
        raise ImportError("Batch processing dependencies not available")
    
    if prompts is None:
        raise ValueError("prompts is required")
    if model_id is None:
        raise ValueError("model_id is required")
    
    if isinstance(prompts, Prompt):
        prompts = [prompts]
    
    if n > 1:
        if len(prompts) > 1:
            raise ValueError("n > 1 is not supported when > 1 prompts are provided")
        prompts = prompts * n

    if use_batch_api:
        batch_kwargs = kwargs.copy()
        callback = batch_kwargs.pop("batch_id_callback", None)

        async def batch_call(prompts: list[Prompt]):
            responses, batch_id = await batch_api(prompts=prompts, model_id=model_id, use_cache=use_cache or False, **batch_kwargs)
            if callback and batch_id:
                callback(batch_id)
            return responses

        if chunk_size is None:
            chunk_size = len(prompts)
        raw_responses = await asyncio.gather(
            *[
                batch_call(prompts[i:i+chunk_size])
                for i in range(0, len(prompts), chunk_size)
            ],
        )
        responses = [item for response_list in raw_responses for item in response_list]
    else:
        kwargs = copy.deepcopy(kwargs)
        responses = await asyncio.gather(
            *[api(prompt=prompt, model_id=model_id, **kwargs) for prompt in prompts]
        )
    
    return responses

class ChatGenerator:
    """Generate synthetic chats for character training."""
    
    def __init__(self, character_spec: CharacterSpec, api_client: APIClient, batch_config: Optional[BatchConfig] = None):
        self.character_spec = character_spec
        self.api_client = api_client
        self.batch_config = batch_config or BatchConfig()
        self.use_batch = self.batch_config.use_batch and BATCH_AVAILABLE
    
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
        """Generate basic question-answer chats using batch processing."""
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
        
        if self.use_batch:
            return await self._generate_basic_chats_batch(num_chats, basic_questions, config)
        else:
            return await self._generate_basic_chats_sequential(num_chats, basic_questions, config)
    
    async def _generate_basic_chats_batch(self, num_chats: int, questions: List[str], config: GenerationConfig) -> List[Chat]:
        """Generate basic chats using batch processing."""
        # Create prompts for batch processing
        prompts = []
        selected_questions = []
        
        for i in range(num_chats):
            question = random.choice(questions)
            selected_questions.append(question)
            
            # Create system message
            system_message = ChatMessage(role=MessageRole.system, content=self.character_spec.system_prompt)
            user_message = ChatMessage(role=MessageRole.user, content=question)
            
            prompt = Prompt(messages=[system_message, user_message])
            prompts.append(prompt)
        
        # Set up batch callback if configured
        batch_callback = None
        if self.batch_config.batch_id_callback:
            batch_callback = self.batch_config.batch_id_callback
        elif self.batch_config.config_path:
            batch_callback = functools.partial(
                _append_batch_id_to_config, 
                self.batch_config.config_path, 
                "basic_chat_generation",
                character_id=self.batch_config.character_id
            )
        
        # Batch generate responses
        responses = await batch_generate(
            api=API,
            batch_api=BATCH_API,
            model_id=config.model,
            prompts=prompts,
            max_tokens=500,
            temperature=config.temperature,
            use_batch_api=True,
            chunk_size=self.batch_config.chunk_size,
            use_cache=self.batch_config.use_cache,
            batch_id_callback=batch_callback,
        )
        
        # Create chat objects
        chats = []
        for i, response in enumerate(responses):
            messages = [
                {"role": "user", "content": selected_questions[i]},
                {"role": "assistant", "content": response.content.strip()}
            ]
            
            chat = Chat(
                messages=messages,
                character_id=self.character_spec.id
            )
            chats.append(chat)
        
        return chats
    
    async def _generate_basic_chats_sequential(self, num_chats: int, questions: List[str], config: GenerationConfig) -> List[Chat]:
        """Generate basic chats sequentially (fallback)."""
        chats = []
        for i in range(num_chats):
            question = random.choice(questions)
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
        """Generate character-specific chats using batch processing."""
        if self.use_batch:
            return await self._generate_character_chats_batch(num_chats, config)
        else:
            return await self._generate_character_chats_sequential(num_chats, config)
    
    async def _generate_character_chats_batch(self, num_chats: int, config: GenerationConfig) -> List[Chat]:
        """Generate character-specific chats using batch processing."""
        # Create scenarios for batch processing
        scenarios = [self._create_character_scenario() for _ in range(num_chats)]
        
        # Generate user messages in batch
        user_message_prompts = []
        for scenario in scenarios:
            prompt = f"""
            Generate a realistic user message for this scenario:
            Type: {scenario['type']}
            Description: {scenario['description']}
            Character trait: {scenario['trait']}
            
            The message should be natural and engaging. Keep it concise (1-2 sentences).
            """
            user_message_prompts.append(Prompt(messages=[ChatMessage(role=MessageRole.user, content=prompt)]))
        
        # Set up batch callback for user messages
        user_batch_callback = None
        if self.batch_config.batch_id_callback:
            user_batch_callback = self.batch_config.batch_id_callback
        elif self.batch_config.config_path:
            user_batch_callback = functools.partial(
                _append_batch_id_to_config, 
                self.batch_config.config_path, 
                "character_user_message_generation",
                character_id=self.batch_config.character_id
            )
        
        # Batch generate user messages
        user_responses = await batch_generate(
            api=API,
            batch_api=BATCH_API,
            model_id=config.model,
            prompts=user_message_prompts,
            max_tokens=100,
            temperature=0.8,
            use_batch_api=True,
            chunk_size=self.batch_config.chunk_size,
            use_cache=self.batch_config.use_cache,
            batch_id_callback=user_batch_callback,
        )
        
        # Generate assistant responses in batch
        assistant_prompts = []
        for i, user_response in enumerate(user_responses):
            system_message = ChatMessage(role=MessageRole.system, content=self.character_spec.system_prompt)
            user_message = ChatMessage(role=MessageRole.user, content=user_response.content.strip())
            assistant_prompts.append(Prompt(messages=[system_message, user_message]))
        
        # Set up batch callback for assistant responses
        assistant_batch_callback = None
        if self.batch_config.batch_id_callback:
            assistant_batch_callback = self.batch_config.batch_id_callback
        elif self.batch_config.config_path:
            assistant_batch_callback = functools.partial(
                _append_batch_id_to_config, 
                self.batch_config.config_path, 
                "character_assistant_response_generation",
                character_id=self.batch_config.character_id
            )
        
        # Batch generate assistant responses
        assistant_responses = await batch_generate(
            api=API,
            batch_api=BATCH_API,
            model_id=config.model,
            prompts=assistant_prompts,
            max_tokens=500,
            temperature=config.temperature,
            use_batch_api=True,
            chunk_size=self.batch_config.chunk_size,
            use_cache=self.batch_config.use_cache,
            batch_id_callback=assistant_batch_callback,
        )
        
        # Create chat objects
        chats = []
        for i, (user_response, assistant_response) in enumerate(zip(user_responses, assistant_responses)):
            messages = [
                {"role": "user", "content": user_response.content.strip()},
                {"role": "assistant", "content": assistant_response.content.strip()}
            ]
            
            chat = Chat(
                messages=messages,
                character_id=self.character_spec.id
            )
            chats.append(chat)
        
        return chats
    
    async def _generate_character_chats_sequential(self, num_chats: int, config: GenerationConfig) -> List[Chat]:
        """Generate character-specific chats sequentially (fallback)."""
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
    
    @classmethod
    def create_with_batch_config(
        cls, 
        character_spec: CharacterSpec, 
        api_client: APIClient,
        config_path: Optional[str] = None,
        character_id: Optional[str] = None,
        chunk_size: Optional[int] = None,
        use_cache: bool = False
    ) -> 'ChatGenerator':
        """Create a ChatGenerator with batch configuration."""
        batch_config = BatchConfig(
            use_batch=True,
            chunk_size=chunk_size,
            use_cache=use_cache,
            config_path=config_path,
            character_id=character_id
        )
        return cls(character_spec, api_client, batch_config)
    
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
