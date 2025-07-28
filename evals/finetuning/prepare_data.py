import json
import os
from typing import List, Dict, Any
import fire
from pydantic import BaseModel, Field
import re

class FineTuningData(BaseModel):
    messages: List[Dict[str, str]]

class SystemMessage(BaseModel):
    role: str = "system"
    content: str

class UserMessage(BaseModel):
    role: str = "user"
    content: str

class AssistantMessage(BaseModel):
    role: str = "assistant"
    content: str

class FineTuningMessage(BaseModel):
    messages: List[SystemMessage | UserMessage | AssistantMessage]

def convert_to_finetuning_format(generated_conversation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts a single GeneratedConversation object from the synthetic dataset
    into the message format required for fine-tuning.
    """
    conversation_log = generated_conversation.get("conversation_log", [])
    if not conversation_log:
        return None

    messages = []
    for msg in conversation_log:
        role = msg.get("role")
        content = msg.get("content")
        if role in ["system", "user", "assistant"] and content:
            # Clean up markdown like **User Response:**
            content = re.sub(r'\*\*\w+\s\w+:\*\*\s*\n', '', content)
            messages.append({"role": role, "content": content})

    # A valid training example should have at least 2 messages
    if not messages or len(messages) < 2:
        return None

    return {"messages": messages}






def prepare_data_for_finetuning(
    input_file: str,
    output_file: str,
):
    """
    Processes a JSONL file of generated conversations and creates a new
    JSONL file formatted for fine-tuning.

    Args:
        input_file: Path to the generated conversations JSONL file.
        output_file: Path to the output JSONL file for fine-tuning.
    """
    print(f"Starting data preparation from: {input_file}")
    
    if not os.path.exists(input_file):
        print(f"Error: File not found at {input_file}")
        return

    # Print the whole input file
    print("\n=== Full Input File Content ===")
    with open(input_file, 'r') as f:
        file_content = f.read()
        print(file_content)
    print("=== End of Input File ===\n")

    finetuning_data = []
    with open(input_file, 'r') as f:
        for idx, line in enumerate(f, 1):
            print(f"\n---\nLine {idx} raw: {line.rstrip()}")
            line = line.strip()
            if not line:
                print(f"Skipping empty line {idx}")
                continue
            try:
                data = json.loads(line)
                print(f"Line {idx} parsed as JSON: {data}")
            except json.JSONDecodeError as e:
                print(f"Warning: Could not decode JSON from line {idx} in {input_file}: {e}")
                continue
            # Skip metadata lines
            if list(data.keys()) == ['metadata']:
                print(f"Line {idx} is metadata, skipping.")
                continue
            # Only process lines with a conversation_log key
            if 'conversation_log' in data:
                clog = data['conversation_log']
                print(f"Line {idx} has conversation_log. Type: {type(clog)}, Length: {len(clog) if isinstance(clog, list) else 'N/A'}")
                if not isinstance(clog, list) or len(clog) == 0:
                    print(f"Skipping line {idx}: conversation_log is not a valid list")
                    continue
                print(f"Sample message: {clog[0] if isinstance(clog, list) and len(clog) > 0 else 'N/A'}")
                # Validate all entries in conversation_log
                valid = True
                for msg in clog:
                    if not (isinstance(msg, dict) and 'role' in msg and 'content' in msg):
                        valid = False
                        print(f"Invalid message in conversation_log: {msg}")
                        break
                if not valid:
                    print(f"Skipping line {idx}: invalid message structure in conversation_log")
                    continue
                # Transform to Together AI format
                transformed = {"messages": [{"role": m["role"], "content": m["content"]} for m in clog]}
                print(f"Line {idx} transformation result: {transformed}")
                finetuning_data.append(transformed)
                print(f"Converted line {idx} to fine-tuning format.")
            else:
                print(f"Skipping line {idx}: no conversation_log key.")

    if not finetuning_data:
        print("No valid data was converted for fine-tuning.")
        return

    with open(output_file, 'w') as f:
        for item in finetuning_data:
            f.write(json.dumps(item) + '\n')

    print(f"Successfully created fine-tuning data at: {output_file}")
    print(f"Total records created: {len(finetuning_data)}")


if __name__ == '__main__':
    fire.Fire(prepare_data_for_finetuning)
