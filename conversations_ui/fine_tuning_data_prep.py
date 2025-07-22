#!/usr/bin/env python3

import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class FinetuningDataset:
    """Data class for fine-tuning dataset."""
    name: str
    description: str
    format: str  # "openai_messages" or "together_text"
    data: List[Dict[str, Any]]
    source_conversations: List[str]
    system_prompt: str
    created_at: str
    stats: Dict[str, Any]

class ConversationToFinetuningConverter:
    """Convert conversation database to fine-tuning datasets."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conversations = self._load_conversations()
        
    def _load_conversations(self) -> List[Dict[str, Any]]:
        """Load conversations from database."""
        conversations = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try evaluation_conversations table first
            try:
                cursor.execute("""
                    SELECT ec.*, ei.text as idea_text, ect.content as context_content
                    FROM evaluation_conversations ec
                    LEFT JOIN evaluation_ideas ei ON ec.idea_id = ei.id
                    LEFT JOIN evaluation_contexts ect ON ec.context_id = ect.id
                    ORDER BY ec.created_at DESC
                """)
                
                for row in cursor.fetchall():
                    conversation = dict(row)
                    
                    # Parse config
                    config = {}
                    if conversation.get('config_json'):
                        try:
                            config = json.loads(conversation['config_json'])
                        except json.JSONDecodeError:
                            pass
                    
                    # Load messages
                    cursor.execute("""
                        SELECT role, content FROM messages 
                        WHERE conversation_id = ? 
                        ORDER BY message_index
                    """, (conversation['id'],))
                    messages = [dict(row) for row in cursor.fetchall()]
                    
                    conversations.append({
                        'id': conversation['id'],
                        'messages': messages,
                        'system_prompt': config.get('system_prompt', ''),
                        'system_prompt_name': config.get('system_prompt_name', ''),
                        'model': config.get('model', ''),
                        'idea_text': conversation.get('idea_text', ''),
                        'context_content': conversation.get('context_content', ''),
                        'created_at': conversation.get('created_at', ''),
                        'type': 'evaluation'
                    })
                    
            except sqlite3.OperationalError:
                # Fallback to regular conversations table
                cursor.execute("""
                    SELECT * FROM conversations 
                    ORDER BY created_at DESC
                """)
                
                for row in cursor.fetchall():
                    conversation = dict(row)
                    
                    # Load messages
                    cursor.execute("""
                        SELECT role, content FROM messages 
                        WHERE conversation_id = ? 
                        ORDER BY message_index
                    """, (conversation['id'],))
                    messages = [dict(row) for row in cursor.fetchall()]
                    
                    conversations.append({
                        'id': conversation['id'],
                        'messages': messages,
                        'system_prompt': conversation.get('system_prompt', ''),
                        'system_prompt_name': conversation.get('system_prompt_name', ''),
                        'model': conversation.get('model', ''),
                        'name': conversation.get('name', ''),
                        'summary': conversation.get('summary', ''),
                        'created_at': conversation.get('created_at', ''),
                        'type': 'regular'
                    })
        
        return conversations
    
    def create_openai_messages_dataset(self, 
                                     conversations: List[Dict[str, Any]] = None,
                                     dataset_name: str = None,
                                     description: str = None) -> FinetuningDataset:
        """Create OpenAI messages format dataset from conversations."""
        
        if conversations is None:
            conversations = self.conversations
        
        if dataset_name is None:
            dataset_name = f"conversations_openai_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if description is None:
            description = f"OpenAI fine-tuning dataset from {len(conversations)} conversations"
        
        data = []
        source_conversations = []
        system_prompts = set()
        
        for conv in conversations:
            if not conv['messages'] or len(conv['messages']) < 2:
                continue  # Skip conversations without proper dialogue
            
            # Build messages array
            messages = []
            
            # Add system prompt if available
            if conv['system_prompt']:
                messages.append({
                    "role": "system",
                    "content": conv['system_prompt']
                })
                system_prompts.add(conv['system_prompt'])
            
            # Add conversation messages
            for msg in conv['messages']:
                if msg['role'] in ['user', 'assistant']:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
            
            # Only include if we have both user and assistant messages
            if len([m for m in messages if m['role'] == 'user']) > 0 and \
               len([m for m in messages if m['role'] == 'assistant']) > 0:
                
                data.append({
                    "messages": messages,
                    "metadata": {
                        "conversation_id": conv['id'],
                        "system_prompt_name": conv.get('system_prompt_name', ''),
                        "model": conv.get('model', ''),
                        "created_at": conv.get('created_at', ''),
                        "type": conv.get('type', 'regular')
                    }
                })
                source_conversations.append(conv['id'])
        
        # Calculate stats
        total_messages = sum(len(item['messages']) for item in data)
        user_messages = sum(len([m for m in item['messages'] if m['role'] == 'user']) for item in data)
        assistant_messages = sum(len([m for m in item['messages'] if m['role'] == 'assistant']) for item in data)
        
        stats = {
            'total_conversations': len(data),
            'total_messages': total_messages,
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'system_prompts_count': len(system_prompts),
            'avg_messages_per_conversation': total_messages / len(data) if data else 0
        }
        
        return FinetuningDataset(
            name=dataset_name,
            description=description,
            format="openai_messages",
            data=data,
            source_conversations=source_conversations,
            system_prompt=list(system_prompts)[0] if len(system_prompts) == 1 else "",
            created_at=datetime.now().isoformat(),
            stats=stats
        )
    
    def create_together_text_dataset(self, 
                                   conversations: List[Dict[str, Any]] = None,
                                   dataset_name: str = None,
                                   description: str = None) -> FinetuningDataset:
        """Create Together AI text format dataset from conversations."""
        
        if conversations is None:
            conversations = self.conversations
        
        if dataset_name is None:
            dataset_name = f"conversations_together_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if description is None:
            description = f"Together AI fine-tuning dataset from {len(conversations)} conversations"
        
        data = []
        source_conversations = []
        system_prompts = set()
        
        for conv in conversations:
            if not conv['messages'] or len(conv['messages']) < 2:
                continue
            
            # Build text format training example
            text_content = ""
            
            # Add system prompt if available
            if conv['system_prompt']:
                text_content += f"<|system|>\n{conv['system_prompt']}\n"
                system_prompts.add(conv['system_prompt'])
            
            # Add conversation messages
            for msg in conv['messages']:
                if msg['role'] == 'user':
                    text_content += f"<|user|>\n{msg['content']}\n"
                elif msg['role'] == 'assistant':
                    text_content += f"<|assistant|>\n{msg['content']}\n"
            
            # Only include if we have both user and assistant messages
            user_count = len([m for m in conv['messages'] if m['role'] == 'user'])
            assistant_count = len([m for m in conv['messages'] if m['role'] == 'assistant'])
            
            if user_count > 0 and assistant_count > 0:
                data.append({
                    "text": text_content.strip(),
                    "metadata": {
                        "conversation_id": conv['id'],
                        "system_prompt_name": conv.get('system_prompt_name', ''),
                        "model": conv.get('model', ''),
                        "created_at": conv.get('created_at', ''),
                        "type": conv.get('type', 'regular')
                    }
                })
                source_conversations.append(conv['id'])
        
        # Calculate stats
        total_chars = sum(len(item['text']) for item in data)
        
        stats = {
            'total_conversations': len(data),
            'total_characters': total_chars,
            'avg_chars_per_conversation': total_chars / len(data) if data else 0,
            'system_prompts_count': len(system_prompts)
        }
        
        return FinetuningDataset(
            name=dataset_name,
            description=description,
            format="together_text",
            data=data,
            source_conversations=source_conversations,
            system_prompt=list(system_prompts)[0] if len(system_prompts) == 1 else "",
            created_at=datetime.now().isoformat(),
            stats=stats
        )
    
    def save_dataset(self, dataset: FinetuningDataset, output_dir: str) -> str:
        """Save fine-tuning dataset to file."""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename
        filename = f"{dataset.name}.jsonl"
        filepath = os.path.join(output_dir, filename)
        
        # Save data in JSONL format
        with open(filepath, 'w') as f:
            for item in dataset.data:
                f.write(json.dumps(item) + '\n')
        
        # Save metadata
        metadata_filepath = os.path.join(output_dir, f"{dataset.name}_metadata.json")
        metadata = {
            'name': dataset.name,
            'description': dataset.description,
            'format': dataset.format,
            'source_conversations': dataset.source_conversations,
            'system_prompt': dataset.system_prompt,
            'created_at': dataset.created_at,
            'stats': dataset.stats,
            'data_file': filename
        }
        
        with open(metadata_filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Dataset saved to: {filepath}")
        print(f"✓ Metadata saved to: {metadata_filepath}")
        print(f"✓ {dataset.stats['total_conversations']} conversations prepared for fine-tuning")
        
        return filepath
    
    def filter_conversations(self, 
                           min_messages: int = 2,
                           max_messages: int = None,
                           system_prompt_name: str = None,
                           model: str = None,
                           conversation_type: str = None) -> List[Dict[str, Any]]:
        """Filter conversations based on criteria."""
        
        filtered = []
        
        for conv in self.conversations:
            # Filter by message count
            if len(conv['messages']) < min_messages:
                continue
                
            if max_messages and len(conv['messages']) > max_messages:
                continue
            
            # Filter by system prompt name
            if system_prompt_name and conv.get('system_prompt_name', '') != system_prompt_name:
                continue
            
            # Filter by model
            if model and conv.get('model', '') != model:
                continue
            
            # Filter by conversation type
            if conversation_type and conv.get('type', '') != conversation_type:
                continue
            
            filtered.append(conv)
        
        return filtered
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """Get statistics about available conversations for fine-tuning."""
        
        stats = {
            'total_conversations': len(self.conversations),
            'conversation_types': {},
            'system_prompts': {},
            'models': {},
            'message_counts': {
                'total': 0,
                'user': 0,
                'assistant': 0,
                'system': 0
            }
        }
        
        for conv in self.conversations:
            # Count by type
            conv_type = conv.get('type', 'regular')
            stats['conversation_types'][conv_type] = stats['conversation_types'].get(conv_type, 0) + 1
            
            # Count by system prompt
            prompt_name = conv.get('system_prompt_name', 'None')
            stats['system_prompts'][prompt_name] = stats['system_prompts'].get(prompt_name, 0) + 1
            
            # Count by model
            model = conv.get('model', 'Unknown')
            stats['models'][model] = stats['models'].get(model, 0) + 1
            
            # Count messages
            for msg in conv['messages']:
                stats['message_counts']['total'] += 1
                role = msg.get('role', 'unknown')
                if role in stats['message_counts']:
                    stats['message_counts'][role] += 1
        
        return stats


def main():
    """Command-line interface for fine-tuning data preparation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare fine-tuning data from conversations")
    parser.add_argument("--db-path", required=True, help="Path to conversations database")
    parser.add_argument("--output-dir", default="./fine_tuning_data", help="Output directory")
    parser.add_argument("--format", choices=["openai", "together", "both"], default="both",
                       help="Output format for fine-tuning data")
    parser.add_argument("--dataset-name", help="Custom dataset name")
    parser.add_argument("--description", help="Dataset description")
    parser.add_argument("--min-messages", type=int, default=2, help="Minimum messages per conversation")
    parser.add_argument("--max-messages", type=int, help="Maximum messages per conversation")
    parser.add_argument("--system-prompt-name", help="Filter by system prompt name")
    parser.add_argument("--model", help="Filter by model")
    parser.add_argument("--conversation-type", help="Filter by conversation type")
    parser.add_argument("--stats-only", action="store_true", help="Only show dataset statistics")
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = ConversationToFinetuningConverter(args.db_path)
    
    if args.stats_only:
        # Show statistics only
        stats = converter.get_dataset_stats()
        print("📊 Dataset Statistics:")
        print(f"Total conversations: {stats['total_conversations']}")
        print(f"\nConversation types:")
        for type_name, count in stats['conversation_types'].items():
            print(f"  {type_name}: {count}")
        print(f"\nSystem prompts:")
        for prompt_name, count in stats['system_prompts'].items():
            print(f"  {prompt_name}: {count}")
        print(f"\nModels:")
        for model, count in stats['models'].items():
            print(f"  {model}: {count}")
        print(f"\nMessage counts:")
        for role, count in stats['message_counts'].items():
            print(f"  {role}: {count}")
        return
    
    # Filter conversations
    filtered_conversations = converter.filter_conversations(
        min_messages=args.min_messages,
        max_messages=args.max_messages,
        system_prompt_name=args.system_prompt_name,
        model=args.model,
        conversation_type=args.conversation_type
    )
    
    print(f"📋 Filtered to {len(filtered_conversations)} conversations")
    
    # Create datasets
    if args.format in ["openai", "both"]:
        openai_dataset = converter.create_openai_messages_dataset(
            conversations=filtered_conversations,
            dataset_name=args.dataset_name,
            description=args.description
        )
        converter.save_dataset(openai_dataset, args.output_dir)
    
    if args.format in ["together", "both"]:
        together_dataset = converter.create_together_text_dataset(
            conversations=filtered_conversations,
            dataset_name=args.dataset_name,
            description=args.description
        )
        converter.save_dataset(together_dataset, args.output_dir)
    
    print(f"✅ Fine-tuning data preparation complete!")


if __name__ == "__main__":
    main()