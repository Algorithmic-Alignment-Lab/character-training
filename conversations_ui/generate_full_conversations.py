#!/usr/bin/env python3

import argparse
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict
from models import ConversationConfig, Conversation, Message
from database import init_db, save_conversation_to_db
from llm_api import get_llm_response


def generate_conversations_from_documents(documents_file: str, model: str, system_prompt: str, output_db: str, config_file: str):
    """Generate conversations from full documents."""
    
    # Load documents
    with open(documents_file, 'r') as f:
        documents = json.load(f)
    
    # Create configuration
    config = ConversationConfig(
        model=model,
        system_prompt=system_prompt,
        user_message_template='{full_document}',
        ideas_filepath=documents_file,
        timestamp=datetime.now()
    )
    
    # Initialize database
    init_db(output_db)
    
    print(f"Generating conversations for {len(documents)} documents...")
    
    # Generate conversations
    conversations = []
    
    for i, doc in enumerate(documents, 1):
        print(f"Generating conversation {i}/{len(documents)}: {doc['title'][:50]}...")
        
        # Use full document content as user message
        messages = [
            Message(role='system', content=system_prompt),
            Message(role='user', content=doc['content'])
        ]
        
        # Get AI response
        api_messages = [{'role': m.role, 'content': m.content} for m in messages]
        response = get_llm_response('', api_messages, model)
        
        # Add response message
        messages.append(Message(role='assistant', content=response))
        
        # Create conversation
        conversation = Conversation(
            id=str(uuid.uuid4()),
            idea_id=doc['id'],
            context_id=doc['id'],
            config=config,
            messages=messages
        )
        
        conversations.append(conversation)
        
        # Save to database
        messages_dict = [{'role': m.role, 'content': m.content} for m in messages]
        save_conversation_to_db(
            conversation.id, 
            messages_dict, 
            system_prompt, 
            model.split('/')[0] if '/' in model else 'unknown',  # provider
            model, 
            f"Red-teaming: {doc['title'][:50]}...",  # summary
            output_db
        )
    
    print(f"Generated {len(conversations)} conversations")
    print(f"Saved to: {output_db}")
    
    # Save config
    with open(config_file, 'w') as f:
        json.dump(config.model_dump(), f, indent=2, default=str)
    
    return conversations


def main():
    parser = argparse.ArgumentParser(description="Generate conversations from full documents")
    parser.add_argument("--documents-file", required=True, help="Path to documents JSON file")
    parser.add_argument("--model", required=True, help="Model to use for conversations")
    parser.add_argument("--system-prompt", required=True, help="System prompt for the AI")
    parser.add_argument("--output-db", required=True, help="Output database file")
    parser.add_argument("--config-file", required=True, help="Output configuration file")
    
    args = parser.parse_args()
    
    # Create output directories
    os.makedirs(os.path.dirname(args.output_db), exist_ok=True)
    os.makedirs(os.path.dirname(args.config_file), exist_ok=True)
    
    # Generate conversations
    conversations = generate_conversations_from_documents(
        args.documents_file,
        args.model,
        args.system_prompt,
        args.output_db,
        args.config_file
    )
    
    print(f"\nCompleted generation of {len(conversations)} conversations")


if __name__ == "__main__":
    main()