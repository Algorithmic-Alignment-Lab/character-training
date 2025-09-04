"""
Prepare a small OpenAI fine-tuning dataset from a large synth_chats.jsonl file.

Usage examples:

python prepare_openai_finetune_data.py \
  --input output_batch_full/clyde_thoughtful_assistant_backstory/synth_chats.jsonl \
  --output-dir evals/finetuning/sample_openai \
  --sample-size 50 \
  --val-size 10

The script streams the input file (works with very large files), finds records with
either ("user_query","assistant_response") or a "messages" list, converts to a
simple prompt/completion JSONL format compatible with OpenAI supervised fine-tuning,
and writes train.jsonl and val.jsonl.

Prompt format (default):
  "Human: <user_query>\nAssistant:"
Completion format (default):
  " <assistant_response>"

This is conservative and should be accepted by the OpenAI fine-tuning tooling.
"""

import argparse
import json
import os
import random
import re
from typing import Optional


def _strip_think_blocks(text: str) -> str:
    """Remove any <think>...</think> blocks (including content) and collapse whitespace."""
    if not text:
        return text
    # Remove <think>...</think> including nested/newline content, case-insensitive
    cleaned = re.sub(r"(?i)<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove any leftover angle-bracketed tags just in case
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    # Collapse multiple spaces/newlines
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def transform_line_to_openai(item: dict) -> Optional[dict]:
    """Return a dict with keys 'prompt' and 'completion' or None if not usable."""
    # First try the simple fields used elsewhere in this repo
    if 'user_query' in item and 'assistant_response' in item:
        user = item.get('user_query', '').strip()
        assistant = item.get('assistant_response', '').strip()
    # Fall back to messages list
    elif 'messages' in item and isinstance(item['messages'], list):
        # Find the last user and assistant pair
        msgs = item['messages']
        user = None
        assistant = None
        # If messages follow role/content structure, pick last user->assistant
        for i in range(len(msgs) - 1, -1, -1):
            if msgs[i].get('role') == 'assistant' and i - 1 >= 0 and msgs[i - 1].get('role') == 'user':
                assistant = msgs[i].get('content', '').strip()
                user = msgs[i - 1].get('content', '').strip()
                break
        # If not found, try first user/assistant
        if user is None:
            user_parts = [m.get('content', '') for m in msgs if m.get('role') == 'user']
            assistant_parts = [m.get('content', '') for m in msgs if m.get('role') == 'assistant']
            if user_parts and assistant_parts:
                user = user_parts[0].strip()
                assistant = assistant_parts[0].strip()
    else:
        return None

    if not user or not assistant:
        return None
    # Strip any <think>...</think> blocks from the extracted text
    user = _strip_think_blocks(user)
    assistant = _strip_think_blocks(assistant)

    # Default behavior returns prompt/completion pair
    prompt = f"Human: {user}\nAssistant:"
    completion = f" {assistant}"
    if not completion.endswith("\n"):
        completion += "\n"

    return {"prompt": prompt, "completion": completion}


def sample_and_write(input_path: str, output_dir: str, sample_size: int = 100, val_size: int = 0):
    os.makedirs(output_dir, exist_ok=True)
    train_path = os.path.join(output_dir, 'train.jsonl')
    val_path = os.path.join(output_dir, 'validation.jsonl') if val_size > 0 else None

    # We'll perform reservoir sampling to handle large files without loading into memory
    reservoir = []
    total_seen = 0

    with open(input_path, 'r') as inf:
        for line in inf:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            conv = transform_line_to_openai(obj)
            if conv is None:
                continue
            total_seen += 1
            if len(reservoir) < sample_size + val_size:
                reservoir.append(conv)
            else:
                # Random replacement
                r = random.randint(0, total_seen - 1)
                if r < (sample_size + val_size):
                    reservoir[r] = conv

    if not reservoir:
        raise RuntimeError(f"No usable conversations found in {input_path}")

    # Shuffle and split
    random.shuffle(reservoir)
    val_samples = reservoir[:val_size]
    train_samples = reservoir[val_size:]

    # Write files
    with open(train_path, 'w') as tf:
        for item in train_samples:
            tf.write(json.dumps(item, ensure_ascii=False) + '\n')
    if val_path:
        with open(val_path, 'w') as vf:
            for item in val_samples:
                vf.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"Wrote {len(train_samples)} training examples to {train_path}")
    if val_path:
        print(f"Wrote {len(val_samples)} validation examples to {val_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Path to synth_chats.jsonl')
    parser.add_argument('--output-dir', default='evals/finetuning/sample_openai', help='Output directory')
    parser.add_argument('--sample-size', type=int, default=100, help='Number of training examples to sample')
    parser.add_argument('--val-size', type=int, default=0, help='Number of validation examples to sample')
    parser.add_argument('--format', choices=['prompt', 'messages'], default='prompt', help='Output format: prompt (prompt/completion JSONL) or messages (chat-style messages JSONL)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    random.seed(args.seed)

    # If messages format is requested, transform reservoir items accordingly
    if args.format == 'prompt':
        sample_and_write(args.input, args.output_dir, args.sample_size, args.val_size)
    else:
        # we'll produce chat-style JSONL where each line is {"messages": [{"role":...,"content":...}, ...]}
        os.makedirs(args.output_dir, exist_ok=True)
        out_train = os.path.join(args.output_dir, 'train.jsonl')
        out_val = os.path.join(args.output_dir, 'validation.jsonl') if args.val_size > 0 else None

        reservoir = []
        total_seen = 0
        with open(args.input, 'r') as inf:
            for line in inf:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Attempt to extract a user/assistant pair
                conv = None
                if 'user_query' in obj and 'assistant_response' in obj:
                    u = _strip_think_blocks(obj.get('user_query', '').strip())
                    a = _strip_think_blocks(obj.get('assistant_response', '').strip())
                    conv = {'messages': [{'role': 'user', 'content': u}, {'role': 'assistant', 'content': a}]}
                elif 'messages' in obj and isinstance(obj['messages'], list):
                    # strip think blocks from each message content
                    msgs = []
                    for m in obj['messages']:
                        role = m.get('role')
                        content = m.get('content', '')
                        if not isinstance(content, str):
                            continue
                        content = _strip_think_blocks(content.strip())
                        msgs.append({'role': role, 'content': content})
                    if msgs:
                        conv = {'messages': msgs}
                if conv is None:
                    continue
                total_seen += 1
                if len(reservoir) < args.sample_size + args.val_size:
                    reservoir.append(conv)
                else:
                    r = random.randint(0, total_seen - 1)
                    if r < (args.sample_size + args.val_size):
                        reservoir[r] = conv

        if not reservoir:
            raise RuntimeError(f"No usable conversations found in {args.input}")

        random.shuffle(reservoir)
        val_samples = reservoir[:args.val_size]
        train_samples = reservoir[args.val_size:]

        with open(out_train, 'w') as tf:
            for item in train_samples:
                tf.write(json.dumps(item, ensure_ascii=False) + '\n')
        if out_val:
            with open(out_val, 'w') as vf:
                for item in val_samples:
                    vf.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"Wrote {len(train_samples)} training conversations to {out_train}")
        if out_val:
            print(f"Wrote {len(val_samples)} validation conversations to {out_val}")


if __name__ == '__main__':
    main()
