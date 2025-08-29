import os
import json
import argparse
import logging
import random
import pandas as pd
from transformers import AutoTokenizer
from datasets import Dataset
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def tokenize_conversations(conversations, model_name, max_length=4096):
    """Tokenize multiple conversations for Together AI fine-tuning format."""
    from transformers import AutoTokenizer
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Ensure we have a pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    input_ids_list = []
    attention_mask_list = []
    labels_list = []
    
    print(f"Tokenizing {len(conversations)} conversations...")
    
    for i, conversation in enumerate(tqdm(conversations)):
        if i % 50 == 0:
            print(f"Processing conversation {i}/{len(conversations)}")
        
        # Check if conversation has the expected structure
        if not isinstance(conversation, dict) or "messages" not in conversation:
            print(f"Warning: Conversation {i} missing messages key, skipping")
            continue
            
        # Use the existing single conversation tokenizer
        try:
            tokenized = tokenize_conversation(conversation, tokenizer, max_length)
            
            if tokenized and 'input_ids' in tokenized:
                input_ids_list.append(tokenized['input_ids'])
                attention_mask_list.append(tokenized['attention_mask'])
                labels_list.append(tokenized['labels'])
        except Exception as e:
            print(f"Warning: Failed to tokenize conversation {i}: {e}")
            continue
    
    print(f"Successfully tokenized {len(input_ids_list)} conversations")
    
    return {
        'input_ids': input_ids_list,
        'attention_mask': attention_mask_list, 
        'labels': labels_list
    }

def tokenize_conversation(conversation, tokenizer, max_length=4096):
    """
    Tokenizes a conversation for Together AI format.
    Returns a dictionary with input_ids, attention_mask, and labels.
    """
    # Apply chat template if available
    if hasattr(tokenizer, 'apply_chat_template') and tokenizer.chat_template is not None:
        try:
            formatted_text = tokenizer.apply_chat_template(
                conversation["messages"], 
                tokenize=False, 
                add_generation_prompt=False
            )
        except Exception as e:
            logging.warning(f"Could not apply chat template: {e}. Falling back to manual formatting.")
            formatted_text = format_conversation_manually(conversation["messages"])
    else:
        formatted_text = format_conversation_manually(conversation["messages"])
    
    # Tokenize the formatted text
    encoding = tokenizer(
        formatted_text,
        truncation=True,
        max_length=max_length,
        padding=False,
        return_tensors=None
    )
    
    input_ids = encoding['input_ids']
    attention_mask = encoding['attention_mask']
    
    # For causal language modeling, labels are the same as input_ids
    # We'll mask the user tokens by setting them to -100
    labels = input_ids.copy()
    
    return {
        'input_ids': input_ids,
        'attention_mask': attention_mask,
        'labels': labels
    }

def format_conversation_manually(messages):
    """
    Manually format conversation when chat template is not available.
    """
    formatted_parts = []
    for message in messages:
        role = message.get('role', '')
        content = message.get('content', '')
        if role == 'user':
            formatted_parts.append(f"User: {content}")
        elif role == 'assistant':
            formatted_parts.append(f"Assistant: {content}")
        elif role == 'system':
            formatted_parts.append(f"System: {content}")
    
    return "\n".join(formatted_parts) + "\n"

def transform_chat(chat_json):
    """
    Transforms a single chat object from the batch generation format
    to the format required for finetuning.

    Input format: {"user_query": "...", "assistant_response": "..."}
    Output format: {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
    """
    user_query = chat_json.get("user_query")
    assistant_response = chat_json.get("assistant_response")

    if not user_query or not assistant_response:
        return None

    return {
        "messages": [
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": assistant_response}
        ]
    }
    """
    Transforms a single chat object from the batch generation format
    to the format required for finetuning.

    Input format: {"user_query": "...", "assistant_response": "..."}
    Output format: {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
    """
    user_query = chat_json.get("user_query")
    assistant_response = chat_json.get("assistant_response")

    if not user_query or not assistant_response:
        return None

    return {
        "messages": [
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": assistant_response}
        ]
    }

def main():
    parser = argparse.ArgumentParser(description="Prepare finetuning data from synthetically generated chats.")
    parser.add_argument("input_file", type=str, help="Path to the input JSONL file with synthetic chats.")
    parser.add_argument("--output_dir", type=str, default="finetuning_data", help="Output directory for train and validation files.")
    parser.add_argument("--train_percentage", type=float, default=1, help="Percentage of conversations to use for training.")
    parser.add_argument("--parquet", action="store_true", help="Output as parquet file instead of JSONL.")
    parser.add_argument("--model", type=str, default="Qwen/Qwen3-1.7B", help="Model name for tokenizer (required for parquet format).")
    parser.add_argument("--max_length", type=int, default=4096, help="Maximum sequence length for tokenization.")
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    all_conversations = []
    try:
        with open(args.input_file, 'r') as f:
            for i, line in enumerate(f):
                try:
                    chat_data = json.loads(line)
                    transformed_chat = transform_chat(chat_data)
                    if transformed_chat:
                        all_conversations.append(transformed_chat)
                except json.JSONDecodeError:
                    logging.warning(f"Could not decode JSON from line {i+1} in {args.input_file}")

    except FileNotFoundError:
        logging.error(f"Input file not found: {args.input_file}")
        return
    except Exception as e:
        logging.error(f"An error occurred while reading {args.input_file}: {e}")
        return

    logging.info(f"Successfully processed {len(all_conversations)} conversations from {args.input_file}.")

    if not all_conversations:
        logging.warning("No valid conversations found. Exiting.")
        return

    random.shuffle(all_conversations)

    train_size = int(len(all_conversations) * args.train_percentage)
    train_conversations = all_conversations[:train_size]
    validation_conversations = all_conversations[train_size:]

    file_extension = "parquet" if args.parquet else "jsonl"
    train_file = os.path.join(args.output_dir, f'train.{file_extension}')
    validation_file = os.path.join(args.output_dir, f'validation.{file_extension}')

    if args.parquet:
        # Convert to tokenized format for parquet
        tokenized_train_data = tokenize_conversations(train_conversations, args.model, args.max_length)
        
        # Create train parquet file
        train_output_path = os.path.join(args.output_dir, "train.parquet")
        
        # Create dataset and save as parquet
        from datasets import Dataset
        train_dataset = Dataset.from_dict(tokenized_train_data)
        train_dataset.save_to_disk(train_output_path.replace('.parquet', ''))
        
        # Also save as parquet directly
        import pandas as pd
        pd.DataFrame(tokenized_train_data).to_parquet(train_output_path, index=False)
        
        print(f"Parquet training data saved to {train_output_path}")
        print(f"Number of tokenized training examples: {len(tokenized_train_data['input_ids'])}")
        
        if len(validation_conversations) > 0:
            tokenized_val_data = tokenize_conversations(validation_conversations, args.model, args.max_length)
            val_output_path = os.path.join(args.output_dir, "validation.parquet")
            
            val_dataset = Dataset.from_dict(tokenized_val_data)
            val_dataset.save_to_disk(val_output_path.replace('.parquet', ''))
            
            pd.DataFrame(tokenized_val_data).to_parquet(val_output_path, index=False)
            print(f"Parquet validation data saved to {val_output_path}")
            print(f"Number of tokenized validation examples: {len(tokenized_val_data['input_ids'])}")
    else:
        with open(train_file, 'w') as f:
            for convo in train_conversations:
                f.write(json.dumps(convo) + '\n')

        with open(validation_file, 'w') as f:
            for convo in validation_conversations:
                f.write(json.dumps(convo) + '\n')

    logging.info(f"Successfully wrote {len(train_conversations)} training conversations to {train_file}")
    logging.info(f"Successfully wrote {len(validation_conversations)} validation conversations to {validation_file}")

    # Show one transcript output
    if train_conversations:
        print("\n--- Sample Formatted Transcript ---")
        print(json.dumps(train_conversations[0], indent=2))
        print("---------------------------------")

    print(f"\nTrain data written to: {os.path.abspath(train_file)}")
    print(f"Validation data written to: {os.path.abspath(validation_file)}")

if __name__ == "__main__":
    main()
