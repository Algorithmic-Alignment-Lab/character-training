#!/usr/bin/env python3

import json
import os
import sys
import sqlite3
from datetime import datetime

# Add conversations_ui to path
sys.path.append('conversations_ui')

from generate_full_documents import DocumentGenerator
from llm_api import get_llm_response
from models import ConversationConfig, Conversation, Message

def create_simple_conversation_db(documents_file, output_db, system_prompt, model):
    """Create conversations database with simple structure."""
    
    # Load documents
    with open(documents_file, 'r') as f:
        documents = json.load(f)
    
    # Create database
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        title TEXT,
        system_prompt TEXT,
        model TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )
    """)
    
    print(f"Generating conversations for {len(documents)} documents...")
    
    for i, doc in enumerate(documents, 1):
        print(f"Generating conversation {i}/{len(documents)}: {doc['title'][:50]}...")
        
        # Generate conversation ID
        conv_id = f"conv_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get AI response
        messages = [{"role": "user", "content": doc['content']}]
        response = get_llm_response(system_prompt, messages, model)
        
        # Save conversation
        cursor.execute("""
        INSERT INTO conversations (id, created_at, title, system_prompt, model)
        VALUES (?, ?, ?, ?, ?)
        """, (conv_id, datetime.now().isoformat(), doc['title'], system_prompt, model))
        
        # Save user message
        cursor.execute("""
        INSERT INTO messages (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """, (conv_id, 'user', doc['content'], datetime.now().isoformat()))
        
        # Save assistant message
        cursor.execute("""
        INSERT INTO messages (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """, (conv_id, 'assistant', response, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    print(f"Saved {len(documents)} conversations to {output_db}")

def main():
    # Configuration
    output_dir = "evaluation_data/agora_redteaming_corrected_20250710_164114"
    
    # Load Agora prompts
    with open('conversations_ui/system_prompts.json', 'r') as f:
        prompts = json.load(f)
    
    agora_original = None
    agora_backstory = None
    
    for persona in prompts['personas']:
        if persona['name'] == "Agora, Collaborative Thinker":
            if persona['version'] == "Original":
                agora_original = persona['system_prompt']
            elif persona['version'] == "With Backstory":
                agora_backstory = persona['system_prompt']
    
    if not agora_original or not agora_backstory:
        print("Error: Could not find Agora system prompts")
        return
    
    # Generate more documents if we only have 1
    documents_file = f"{output_dir}/full_documents.json"
    if os.path.exists(documents_file):
        with open(documents_file, 'r') as f:
            docs = json.load(f)
        
        if len(docs) < 10:
            print(f"Only {len(docs)} documents found. Generating more...")
            generator = DocumentGenerator(agora_original, 10, 
                "red-teaming character traits for collaborative AI assistant - create full realistic documents")
            new_docs = generator.generate_full_documents("anthropic/claude-sonnet-4-20250514")
            
            with open(documents_file, 'w') as f:
                json.dump(new_docs, f, indent=2)
            print(f"Generated {len(new_docs)} new documents")
    
    # Generate conversations for both versions
    model = "openrouter/qwen/qwen2.5-vl-32b-instruct"
    
    print("\n=== Generating Original Agora Conversations ===")
    create_simple_conversation_db(
        documents_file,
        f"{output_dir}/agora_original_conversations.db",
        agora_original,
        model
    )
    
    print("\n=== Generating Backstory Agora Conversations ===")
    create_simple_conversation_db(
        documents_file,
        f"{output_dir}/agora_backstory_conversations.db", 
        agora_backstory,
        model
    )
    
    print("\n=== Conversations Generated Successfully! ===")
    print(f"Results saved in: {output_dir}")
    print("\nNext steps:")
    print("1. Run evaluation: cd conversations_ui && python judge_conversations.py ...")
    print("2. View in Streamlit: cd conversations_ui && streamlit run streamlit_chat.py")

if __name__ == "__main__":
    main()