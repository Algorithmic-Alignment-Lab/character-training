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
    assistant_persona = generated_conversation.get("metadata", {}).get("assistant_persona", {})
    system_prompt = assistant_persona.get("system_prompt")

    if not system_prompt or not conversation_log:
        return None

    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_log:
        role = "user" if msg.get('role') == 'user' else "assistant"
        content = msg.get('content')
        if content:
            messages.append({"role": role, "content": content})

    # A valid training example should end with an assistant's message.
    if messages and messages[-1]["role"] == "user":
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

    finetuning_data = []
    with open(input_file, 'r') as f:
        for line in f:
            try:
                # Each line is a JSON representation of a ConversationDataset
                data = json.loads(line)
                # It contains a list of conversations
                for conversation in data.get("conversations", []):
                    converted = convert_to_finetuning_format(conversation)
                    if converted:
                        finetuning_data.append(converted)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from a line in {input_file}")
                continue

    if not finetuning_data:
        print("No valid data was converted for fine-tuning.")
        return

    # Write to JSONL file
    with open(output_file, 'w') as f:
        for item in finetuning_data:
            f.write(json.dumps(item) + '
')

    print(f"Successfully created fine-tuning data at: {output_file}")
    print(f"Total records created: {len(finetuning_data)}")


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

    finetuning_data = []
    with open(input_file, 'r') as f:
        for line in f:
            try:
                # Each line is a JSON representation of a ConversationDataset
                data = json.loads(line)
                # It contains a list of conversations
                for conversation in data.get("conversations", []):
                    converted = convert_to_finetuning_format(conversation)
                    if converted:
                        finetuning_data.append(converted)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from a line in {input_file}")
                continue

    if not finetuning_data:
        print("No valid data was converted for fine-tuning.")
        return

    # Write to JSONL file
    with open(output_file, 'w') as f:
        for item in finetuning_data:
            f.write(json.dumps(item) + '\n')

    print(f"Successfully created fine-tuning data at: {output_file}")
    print(f"Total records created: {len(finetuning_data)}")


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

    finetuning_data = []
    with open(input_file, 'r') as f:
        for line in f:
            try:
                # Each line is a JSON representation of a ConversationDataset
                data = json.loads(line)
                # It contains a list of conversations
                for conversation in data.get("conversations", []):
                    converted = convert_to_finetuning_format(conversation)
                    if converted:
                        finetuning_data.append(converted)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from a line in {input_file}")
                continue

    if not finetuning_data:
        print("No valid data was converted for fine-tuning.")
        return

    # Write to JSONL file
    with open(output_file, 'w') as f:
        for item in finetuning_data:
            f.write(json.dumps(item) + '\n')

    print(f"Successfully created fine-tuning data at: {output_file}")
    print(f"Total records created: {len(finetuning_data)}")


if __name__ == '__main__':
    fire.Fire(prepare_data_for_finetuning)
