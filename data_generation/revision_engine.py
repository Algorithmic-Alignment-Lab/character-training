"""
Revision engine for improving generated conversations.
"""
from typing import List, Dict, Any
from shared.api_client import APIClient
from shared.models import Chat

class RevisionEngine:
    """Engine for revising and improving generated conversations."""
    
    def __init__(self, api_client: APIClient, revision_model: str = "claude-sonnet-4-20250514"):
        self.api_client = api_client
        self.revision_model = revision_model
    
    async def revise_conversations(self, chats: List[Chat]) -> List[Chat]:
        """Revise a list of conversations to improve quality."""
        print(f"🔄 Revising {len(chats)} conversations...")
        
        revised_chats = []
        for i, chat in enumerate(chats):
            try:
                revised_chat = await self.revise_single_conversation(chat)
                revised_chats.append(revised_chat)
                print(f"   Revised chat {i+1}/{len(chats)}")
            except Exception as e:
                print(f"Warning: Failed to revise chat {i+1}: {e}")
                revised_chats.append(chat)  # Keep original if revision fails
        
        print(f"✅ Revised {len(revised_chats)} conversations")
        return revised_chats
    
    async def revise_single_conversation(self, chat: Chat) -> Chat:
        """Revise a single conversation."""
        if len(chat.messages) < 2:
            return chat
        
        # Get the assistant's response
        assistant_message = chat.messages[-1]["content"]
        user_message = chat.messages[-2]["content"]
        
        # Create revision prompt
        revision_prompt = f"""
        Please improve this assistant response to make it more helpful, clear, and engaging:
        
        User: {user_message}
        Assistant: {assistant_message}
        
        Provide an improved version that:
        1. Is more helpful and informative
        2. Is clearer and easier to understand
        3. Is more engaging and conversational
        4. Maintains the same core information
        
        Improved response:
        """
        
        messages = [{"role": "user", "content": revision_prompt}]
        
        result = await self.api_client.call_llm_api(
            messages=messages,
            model=self.revision_model,
            temperature=0.3,
            max_tokens=300
        )
        
        # Create revised chat
        revised_messages = chat.messages.copy()
        revised_messages[-1]["content"] = result.response_text.strip()
        
        return Chat(
            messages=revised_messages,
            character_id=chat.character_id
        )
    
    async def enhance_quality(self, chat: Chat) -> Chat:
        """Enhance the quality of a conversation."""
        return await self.revise_single_conversation(chat)
