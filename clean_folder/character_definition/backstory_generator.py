"""
Backstory generation for characters.
"""
from typing import Optional
from shared.api_client import APIClient

class BackstoryGenerator:
    """Generate character backstories."""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    async def generate_backstory(self, character_name: str, 
                               character_description: str,
                               traits: Optional[list] = None) -> str:
        """Generate a backstory for a character."""
        traits_text = ""
        if traits:
            traits_text = f"\nCharacter traits: {', '.join(traits)}"
        
        prompt = f"""
        Generate a compelling backstory for this character:
        
        Name: {character_name}
        Description: {character_description}{traits_text}
        
        Create a backstory that:
        1. Explains how the character developed their personality and traits
        2. Provides context for their behavior and motivations
        3. Is consistent with their description and traits
        4. Is engaging and adds depth to the character
        5. Is 2-3 paragraphs long
        
        Return only the backstory text.
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            result = await self.api_client.call_llm_api(
                messages=messages,
                model="gpt-4o",
                temperature=0.7,
                max_tokens=600
            )
            
            return result.response_text.strip()
            
        except Exception as e:
            print(f"Warning: Failed to generate backstory: {e}")
            return ""
    
    async def enhance_existing_backstory(self, backstory: str, 
                                       character_description: str) -> str:
        """Enhance an existing backstory."""
        prompt = f"""
        Enhance this character backstory to make it more compelling and detailed:
        
        Character description: {character_description}
        
        Current backstory: {backstory}
        
        Improve the backstory by:
        1. Adding more specific details and context
        2. Making it more engaging and memorable
        3. Ensuring it aligns with the character description
        4. Adding depth and complexity while maintaining consistency
        
        Return only the enhanced backstory.
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            result = await self.api_client.call_llm_api(
                messages=messages,
                model="gpt-4o",
                temperature=0.6,
                max_tokens=700
            )
            
            return result.response_text.strip()
            
        except Exception as e:
            print(f"Warning: Failed to enhance backstory: {e}")
            return backstory
