import os
import json
import argparse
import glob
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_messages_from_events(events, keep_system_prompt=False):
    messages = []
    if not events:
        return messages

    for event in events:
        message = event.get('edit', {}).get('message', {})
        if message and 'content' in message and 'name' in message:
            role = None
            name = message.get('name')
            content = message['content']

            if not content or name in ["Target Thinking", "Evaluator Thinking"]:
                continue

            if name in ['Evaluator', 'user']:
                role = 'user'
            elif name in ['Target', 'assistant']:
                role = 'assistant'
            elif name == 'Target System Prompt' and keep_system_prompt:
                role = 'system'
            
            if '<thinking>' in content:
                content = content.split('</thinking>')[-1].strip()
            if '<system_prompt>' in content:
                content = content.split('</system_prompt>')[-1].strip()
            if '<END>' in content:
                content = content.replace('<END>', '').strip()

            if role and content:
                messages.append({"role": role, "content": content})
    
    if not messages:
        return []

    merged = [messages[0]]
    for msg in messages[1:]:
        if msg['role'] == merged[-1]['role']:
            if msg['content'] not in merged[-1]['content']:
                merged[-1]['content'] += '\n\n' + msg['content']
        else:
            merged.append(msg)
    return merged

def process_transcript_file(file_path, keep_system_prompt=False):
    conversations = []
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if 'events' in data:
                messages = extract_messages_from_events(data.get('events', []), keep_system_prompt)
                if messages:
                    conversations.append({"messages": messages})
                    logging.info(f"  - Extracted conversation from {file_path}")
    except Exception as e:
        logging.error(f"Error processing transcript file {file_path}: {e}")
    return conversations

def main():
    parser = argparse.ArgumentParser(description="Gather all conversations from transcript directories.")
    parser.add_argument("transcript_folders", type=str, nargs='+', help="Root folders for transcripts.")
    parser.add_argument("--output_dir", type=str, default="finetuning_data", help="Output directory for train and validation files.")
    parser.add_argument("--train_percentage", type=float, default=0.8, help="Percentage of conversations to use for training.")
    parser.add_argument("--keep_system_prompt", action='store_true', help="Include the system prompt in the training data.")
    parser.add_argument("--min_score", type=float, default=8.0, help="Minimum eval_success_score required (default: 8.0)")
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    all_conversations = []
    for folder in args.transcript_folders:
        logging.info(f"--- Scanning folder: {folder} ---")
        json_files = glob.glob(os.path.join(folder, "**", "transcript_*.json"), recursive=True)
        logging.info(f"Found {len(json_files)} transcript files in {folder}")

        # Prefilter transcripts by eval_success_score
        kept_files = []
        dropped_count = 0
        for file_path in json_files:
            with open(file_path) as f:
                try:
                    data = json.load(f)
                    score = data.get('metadata', {}).get('judge_output', {}).get('scores', {}).get('eval_success_score', -1.0)
                except (json.JSONDecodeError, KeyError):
                    score = -1.0
            if score >= args.min_score:
                kept_files.append(file_path)
            else:
                dropped_count += 1
        
        logging.info(f"Prefiltering transcripts: kept {len(kept_files)}, dropped {dropped_count} files.")

        if not kept_files:
            logging.warning(f"No transcript files met the minimum score of {args.min_score} in {folder}")
            continue

        # Group transcripts by base name (e.g., 'transcript_65')
        grouped_transcripts = {}
        for file_path in kept_files:
            file_name = os.path.basename(file_path)
            # Group by base name, e.g., 'transcript_65' from 'transcript_65_1.json'
            parts = file_name.replace('.json', '').split('_')
            if len(parts) > 1 and parts[-1].isdigit():
                base_name = "_".join(parts[:-1])
            else:
                base_name = file_name.replace('.json', '')
            
            if base_name not in grouped_transcripts:
                grouped_transcripts[base_name] = []
            grouped_transcripts[base_name].append(file_path)

        logging.info(f"Found {len(grouped_transcripts)} conversation groups in {folder}. ")
        
        best_transcripts = []
        for base_name, files in grouped_transcripts.items():
            if len(files) == 1:
                best_transcripts.append(files[0])
                continue

            best_file = None
            max_score = -1.0

            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        # The score is in the 'judge_output' dictionary
                        print(data.get('metadata'))
                        score = data.get('metadata', {}).get('judge_output', {}).get('scores', {}).get('eval_success_score', -1.0)
                        if score > max_score:
                            max_score = score
                            best_file = file_path
                except Exception as e:
                    logging.error(f"Error processing {file_path} for scoring: {e}")
            
            if best_file:
                best_transcripts.append(best_file)
                logging.info(f"  - Selected {os.path.basename(best_file)} for group {base_name} with score {max_score}")
            elif files:
                # Fallback to the first file if no scores are found
                best_transcripts.append(files[0])
                logging.warning(f"  - Could not determine best transcript for {base_name}, picking first one.")

        logging.info(f"Selected {len(best_transcripts)} best transcripts from {folder}.")

        for file_path in best_transcripts:
            all_conversations.extend(process_transcript_file(file_path, args.keep_system_prompt))

    logging.info(f"--- Finished scanning all folders ---")
    logging.info(f"Found a total of {len(all_conversations)} conversations.")
    
    if not all_conversations:
        logging.warning("No conversations found. Exiting.")
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
        print("""
--- Sample Formatted Transcript ---""")
        print(json.dumps(train_conversations[0], indent=2))
        print("""---------------------------------""")

    print(f"\nTrain data written to: {os.path.abspath(train_file)}")
    print(f"Validation data written to: {os.path.abspath(validation_file)}")

if __name__ == "__main__":
    main()

