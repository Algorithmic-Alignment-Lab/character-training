import os
import json
import argparse
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

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

def main():
    parser = argparse.ArgumentParser(description="Prepare finetuning data from synthetically generated chats.")
    parser.add_argument("input_file", type=str, help="Path to the input JSONL file with synthetic chats.")
    parser.add_argument("--output_dir", type=str, default="finetuning_data", help="Output directory for train and validation files.")
    parser.add_argument("--train_percentage", type=float, default=0.9, help="Percentage of conversations to use for training.")
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

    train_file = os.path.join(args.output_dir, 'train.jsonl')
    validation_file = os.path.join(args.output_dir, 'validation.jsonl')

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
