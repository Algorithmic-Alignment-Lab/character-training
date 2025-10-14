"""
Trait extraction from character descriptions.
"""
from typing import List, Dict, Any
from shared.api_client import APIClient

class TraitExtractor:
    """Extract character traits from descriptions."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    async def extract_traits(self, character_description: str) -> List[str]:
        """Extract traits from a character description."""
        prompt = f"""
        Analyze this character description and extract the key personality traits and behavioral characteristics:
        
        {character_description}
        
        Return a list of 3-7 specific traits that define this character's personality and behavior.
        Each trait should be a clear, actionable description of how the character behaves.
        
        Format as a JSON list of strings.
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            result = await self.api_client.call_llm_api(
                messages=messages,
                model="gpt-4o",
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the response
            import json
            traits = json.loads(result.response_text)
            
            if isinstance(traits, list):
                return [trait.strip() for trait in traits if trait.strip()]
            else:
                return []
                
        except Exception as e:
            print(f"Warning: Failed to extract traits: {e}")
            return []
    
    async def extract_key_facts(self, character_description: str) -> List[str]:
        """Extract key facts about the character."""
        prompt = f"""
        Analyze this character description and extract the key facts and background information:
        
        {character_description}
        
        Return a list of 3-5 important facts about this character's background, purpose, or defining characteristics.
        Each fact should be a clear, factual statement about the character.
        
        Format as a JSON list of strings.
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            result = await self.api_client.call_llm_api(
                messages=messages,
                model="gpt-4o",
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the response
            import json
            facts = json.loads(result.response_text)
            
            if isinstance(facts, list):
                return [fact.strip() for fact in facts if fact.strip()]
            else:
                return []
                
        except Exception as e:
            print(f"Warning: Failed to extract key facts: {e}")
            return []
    
    async def enhance_character_description(self, character_description: str) -> str:
        """Enhance a character description with more detail."""
        prompt = f"""
        Enhance this character description to make it more detailed and comprehensive:
        
        {character_description}
        
        Provide an improved version that:
        1. Is more detailed and specific
        2. Clearly defines the character's personality and behavior
        3. Includes their purpose and goals
        4. Is suitable for use as a system prompt for an AI assistant
        
        Return only the enhanced description.
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            result = await self.api_client.call_llm_api(
                messages=messages,
                model="gpt-4o",
                temperature=0.5,
                max_tokens=800
            )
            
            return result.response_text.strip()
            
        except Exception as e:
            print(f"Warning: Failed to enhance description: {e}")
            return character_description
