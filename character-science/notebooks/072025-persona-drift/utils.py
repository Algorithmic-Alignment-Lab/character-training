import json
import glob
from typing import List, Dict, Any
import torch

def load_jsons(data_dir: str = "data") -> List[Dict[str, Any]]:
    """Load all JSON files from the specified directory"""
    json_files = glob.glob(f"{data_dir}/*.json")
    conversations = []
    
    for file_path in json_files:
        with open(file_path, 'r') as f:
            data = json.load(f)
            data['_filename'] = file_path.split('/')[-1]
            conversations.append(data)
    
    print(f"Loaded {len(conversations)} JSON files")
    return conversations

def format_conversations_with_thinking(conversations):
      """Keep original structure but format the conversation messages"""
      formatted_conversations = []

      for conv in conversations:
          formatted_conv = conv.copy() # keep data from other keys 
          formatted_conv['conversation'] = [
              {
                  'role': c['role'],
                  'content': (f"<thinking>\n{c['thinking']}\n</thinking>\n\n" if c.get('thinking') else "") +
  c['content']
              }
              for c in conv['conversation']
          ]
          formatted_conversations.append(formatted_conv)

      return formatted_conversations

def extract_activations_from_conversation(messages, tokenizer, model, layer_idx=-1):
    """
    Tokenize conversation and extract activations
    
    Returns:
        tokens: [seq_len] token ids
        activations: [seq_len, hidden_dim] activation vectors
    """
    tokens = tokenizer.apply_chat_template(
        messages,
        tokenize = True,
        return_tensors = "pt"
    )

    with torch.no_grad():
        outputs = model(
            tokens,
            output_hidden_states = True, 
            use_cache = False # no generations
        )

    # taking activations from last layer for now – eventually may want to do cross-layer analysis
    # outputs.hidden_states is a tuple of [batch, seq_len, hidden_dim]
    if layer_idx == -1:
        layer_activations = outputs.hidden_states[-1]  
    else:
        layer_activations = outputs.hidden_states[layer_idx]

    return tokens.squeeze(0), layer_activations.squeeze(0)

def process_all_conversations(formatted_conversations, tokenizer, model, save_path = "conversation_activations.pt"):
    results = []
    
    for i, conv in enumerate(formatted_conversations):
        print(f"Processing conversation {i+1}/{len(formatted_conversations)}: {conv.get('_filename', 'unknown')}")
        
        tokens, activations = extract_activations_from_conversation(
            conv['conversation'], tokenizer, model
        )
        
        user_turns = sum(1 for msg in conv['conversation'] if msg['role'] == 'user')
        assistant_turns = sum(1 for msg in conv['conversation'] if msg['role'] == 'assistant')
        
        result = {
            'filename': conv.get('_filename', f'conversation_{i}'),
            'original_metadata': conv.get('metadata', {}),
            'user_turns': user_turns,
            'assistant_turns': assistant_turns,
            'total_messages': len(conv['conversation']),
            'tokens': tokens,
            'activations': activations,
            'num_tokens': len(tokens),
            'hidden_dim': activations.shape[1],
            'conversation_index': i
        }
        results.append(result)
    
    torch.save(results, save_path)
    print(f"Saved {len(results)} conversations to {save_path}")
    
    total_tokens = sum(r['num_tokens'] for r in results)
    total_user_turns = sum(r['user_turns'] for r in results)
    total_assistant_turns = sum(r['assistant_turns'] for r in results)
    
    print(f"Summary: {total_tokens} total tokens, {total_user_turns} user turns, {total_assistant_turns} assistant turns")
    
    return results