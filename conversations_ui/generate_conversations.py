#!/usr/bin/env python3

import argparse
import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Any
from models import ConversationConfig, Conversation, Message
from llm_api import get_llm_response
from database import init_db


class ConversationGenerator:
    def __init__(self, config: ConversationConfig):
        self.config = config

    def generate_conversation(self, idea_data: Dict[str, Any], model: str = "claude-3-5-sonnet-20241022") -> Conversation:
        """Generate a conversation using the idea and context data."""
        user_message = self.format_user_message(idea_data)
        
        # Create the conversation messages
        messages = [
            Message(role="system", content=self.config.system_prompt),
            Message(role="user", content=user_message)
        ]
        
        # Get AI response
        ai_response = get_llm_response(
            self.config.system_prompt,
            [{"role": "user", "content": user_message}],
            model
        )
        
        messages.append(Message(role="assistant", content=ai_response))
        
        # Create conversation object
        conversation = Conversation(
            id=str(uuid.uuid4()),
            idea_id=idea_data.get('id', ''),
            context_id=idea_data.get('context_id', ''),
            config=self.config,
            messages=messages
        )
        
        return conversation

    def format_user_message(self, idea_data: Dict[str, Any]) -> str:
        """Format the user message template with idea and context data."""
        message = self.config.user_message_template
        
        # Replace template variables
        message = message.replace('{idea}', idea_data.get('text', ''))
        
        # Replace context variables (supports multiple context pages)
        for key, value in idea_data.items():
            if key.startswith('context_'):
                placeholder = '{' + key + '}'
                if placeholder in message:
                    message = message.replace(placeholder, str(value))
        
        return message


def generate_db_name(model: str, ideas_summary: str, config_params: Dict[str, Any], 
                     model_api: str = "claude-3-5-sonnet-20241022") -> str:
    """Generate a descriptive database name using AI."""
    prompt = f"""Generate a descriptive 5-word database name for this AI evaluation run:

Model: {model}
Ideas Summary: {ideas_summary}
Config: {json.dumps(config_params, indent=2)}

The name should:
- Be exactly 5 words
- Be descriptive and memorable
- Use underscores instead of spaces
- Be suitable as a filename
- Capture the essence of this evaluation

Examples:
- "honest_character_consistency_evaluation_run"
- "empathetic_ai_response_quality_test"
- "complex_moral_reasoning_benchmark_study"

Respond with only the 5-word name, nothing else."""

    messages = [{"role": "user", "content": prompt}]
    response = get_llm_response("", messages, model_api)
    
    # Clean and validate the response
    name = response.strip().lower()
    name = name.replace(' ', '_')
    name = ''.join(c for c in name if c.isalnum() or c == '_')
    
    # Validate it's roughly 5 words
    words = name.split('_')
    if len(words) != 5:
        # Fallback to timestamp-based name (continuous timestamp for single segment)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"evaluation_run_{timestamp}"
    
    return name


def load_ideas_with_contexts(filepath: str) -> List[Dict[str, Any]]:
    """Load ideas with contexts from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def create_ideas_summary(ideas: List[Dict[str, Any]]) -> str:
    """Create a summary of the ideas for naming purposes."""
    if not ideas:
        return "empty_ideas_set"
    
    # Take first few ideas and create a brief summary
    first_ideas = ideas[:3]
    summary_parts = []
    
    for idea in first_ideas:
        text = idea.get('text', '')[:50]  # First 50 chars
        summary_parts.append(text)
    
    summary = "; ".join(summary_parts)
    return summary


def save_conversations_to_db(conversations: List[Conversation], db_path: str):
    """Save conversations to the database."""
    init_db(db_path)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        for conv in conversations:
            # Save conversation
            cursor.execute("""
            INSERT INTO evaluation_conversations 
            (id, idea_id, context_id, config_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (
                conv.id,
                conv.idea_id,
                conv.context_id,
                json.dumps(conv.config.model_dump(), default=str),
                conv.created_at.isoformat()
            ))
            
            # Save messages to the regular messages table for compatibility
            for i, msg in enumerate(conv.messages):
                cursor.execute("""
                INSERT INTO messages (id, conversation_id, message_index, role, content)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    conv.id,
                    i,
                    msg.role,
                    msg.content
                ))
        
        conn.commit()


def save_config_to_json(config: ConversationConfig, output_dir: str):
    """Save the configuration to a JSON file for reference."""
    config_file = os.path.join(output_dir, "config.json")
    with open(config_file, 'w') as f:
        json.dump(config.model_dump(), f, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(description="Generate conversations from ideas and contexts")
    parser.add_argument("--ideas-file", required=True, help="Path to ideas with contexts JSON file")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022", help="Model to use for conversations")
    parser.add_argument("--system-prompt", required=True, help="System prompt for the AI")
    parser.add_argument("--user-message-template", required=True, 
                       help="User message template (use {idea}, {context_N} placeholders)")
    parser.add_argument("--output-dir", help="Output directory (defaults to auto-generated)")
    
    args = parser.parse_args()
    
    # Load ideas with contexts
    print(f"Loading ideas from: {args.ideas_file}")
    ideas = load_ideas_with_contexts(args.ideas_file)
    print(f"Loaded {len(ideas)} ideas with contexts")
    
    # Create configuration
    config = ConversationConfig(
        model=args.model,
        system_prompt=args.system_prompt,
        user_message_template=args.user_message_template,
        ideas_filepath=args.ideas_file
    )
    
    # Generate database name
    ideas_summary = create_ideas_summary(ideas)
    config_params = {
        "model": args.model,
        "system_prompt_length": len(args.system_prompt),
        "template_length": len(args.user_message_template)
    }
    
    db_name = generate_db_name(args.model, ideas_summary, config_params)
    print(f"Generated database name: {db_name}")
    
    # Set up output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"evaluation_data/{timestamp}"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Database path
    db_path = os.path.join(output_dir, f"{db_name}.db")
    print(f"Output directory: {output_dir}")
    print(f"Database: {db_path}")
    
    # Generate conversations
    generator = ConversationGenerator(config)
    conversations = []
    
    for i, idea_data in enumerate(ideas, 1):
        print(f"Generating conversation {i}/{len(ideas)} for idea: {idea_data.get('text', '')[:50]}...")
        conversation = generator.generate_conversation(idea_data, args.model)
        conversations.append(conversation)
    
    # Save to database
    save_conversations_to_db(conversations, db_path)
    
    # Save configuration
    save_config_to_json(config, output_dir)
    
    print(f"\nConversation generation complete!")
    print(f"Generated {len(conversations)} conversations")
    print(f"Saved to database: {db_path}")
    print(f"Configuration saved to: {os.path.join(output_dir, 'config.json')}")
    
    # Print summary of conversations
    print(f"\nGenerated conversations:")
    for i, conv in enumerate(conversations, 1):
        assistant_msg = next((msg for msg in conv.messages if msg.role == "assistant"), None)
        if assistant_msg:
            preview = assistant_msg.content[:100].replace('\n', ' ')
            print(f"{i}. {preview}...")


if __name__ == "__main__":
    main()