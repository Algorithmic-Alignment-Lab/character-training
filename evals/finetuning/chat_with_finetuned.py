#!/usr/bin/env python3
"""
Interactive CLI to chat with a fine-tuned OpenAI model.

Usage examples:

export OPENAI_API_KEY="sk-..."
python evals/finetuning/chat_with_finetuned.py --model-id ft:... --system "You are a helpful assistant called Clyde." 

Commands available in the REPL:
  /exit        - exit the REPL
  /reset       - clear conversation history
  /history     - print current conversation history
  /save <file> - save conversation history to a JSONL file
  /help        - show this help

"""
import os
import sys
import argparse
import json
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


def print_help():
    print("Commands:")
    print("  /exit        - exit the REPL")
    print("  /reset       - clear conversation history")
    print("  /history     - print current conversation history")
    print("  /save <file> - save conversation history to a JSONL file")
    print("  /help        - show this help")


def save_history(history, path):
    with open(path, 'w') as f:
        for msg in history:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    print(f"Saved {len(history)} messages to {path}")


def chat_loop(model_id, system_prompt=None, temperature=0.2, max_tokens=512):
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        print('Error: OPENAI_API_KEY not set in environment')
        sys.exit(1)

    client = OpenAI(api_key=key)

    history = []
    if system_prompt:
        history.append({"role": "system", "content": system_prompt})

    print(f"Chatting with model: {model_id}")
    print("Type /help for commands. Press Ctrl-C or type /exit to quit.")

    try:
        while True:
            try:
                user_input = input('\nYou: ').strip()
            except EOFError:
                print('\nReceived EOF, exiting.')
                break

            if not user_input:
                continue

            if user_input.startswith('/'):
                parts = user_input.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else None
                if cmd == '/exit':
                    break
                elif cmd == '/reset':
                    history = []
                    if system_prompt:
                        history.append({"role": "system", "content": system_prompt})
                    print('Conversation history cleared.')
                    continue
                elif cmd == '/history':
                    print('\nConversation history:')
                    for m in history:
                        print(f"[{m['role']}] {m['content']}")
                    continue
                elif cmd == '/save':
                    if not arg:
                        print('Usage: /save filename.jsonl')
                        continue
                    save_history(history, arg)
                    continue
                elif cmd == '/help':
                    print_help()
                    continue
                else:
                    print('Unknown command. Type /help for commands.')
                    continue

            # Normal user message
            history.append({"role": "user", "content": user_input})

            try:
                resp = client.chat.completions.create(
                    model=model_id,
                    messages=history,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                print(f"Error from API: {e}")
                # remove last user message to avoid duplication if desired
                continue

            # Parse response -- support different SDK shapes
            try:
                assistant_msg = resp.choices[0].message.content
            except Exception:
                # fallback to dict style
                try:
                    assistant_msg = resp['choices'][0]['message']['content']
                except Exception:
                    assistant_msg = str(resp)

            print('\nAssistant:')
            print(assistant_msg)
            history.append({"role": "assistant", "content": assistant_msg})

    except KeyboardInterrupt:
        print('\nInterrupted, exiting.')


def main():
    parser = argparse.ArgumentParser(description='Interactive chat with a fine-tuned OpenAI model')
    parser.add_argument('--model-id', help='Fine-tuned model id (or base model) to chat with', default='ft:gpt-4.1-nano-2025-04-14:scale-safety-research-1:clyde-test-msgs-20250902:CBVdS3st')
    parser.add_argument('--system', default=None, help='Optional system prompt')
    parser.add_argument('--temperature', type=float, default=0.2, help='Sampling temperature')
    parser.add_argument('--max-tokens', type=int, default=512, help='Max tokens for completions')
    parser.add_argument('--message', default=None, help='If provided, run a single message and exit (non-interactive)')
    args = parser.parse_args()

    if args.message:
        key = os.getenv('OPENAI_API_KEY')
        if not key:
            print('Error: OPENAI_API_KEY not set in environment')
            sys.exit(1)
        client = OpenAI(api_key=key)
        messages = []
        if args.system:
            messages.append({"role": "system", "content": args.system})
        messages.append({"role": "user", "content": args.message})
        resp = client.chat.completions.create(
            model=args.model_id,
            messages=messages,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        try:
            print(resp.choices[0].message.content)
        except Exception:
            print(json.dumps(resp, indent=2, default=str))
        return

    chat_loop(args.model_id, system_prompt=args.system, temperature=args.temperature, max_tokens=args.max_tokens)


if __name__ == '__main__':
    main()
