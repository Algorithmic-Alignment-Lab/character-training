
import json
import os

folder1_path = 'folder1'
folder2_path = 'folder2'

folder1_conversations = {}
if os.path.exists(folder1_path):
    for filename in os.listdir(folder1_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder1_path, filename)
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    conversation_id = data.get('conversation_id')
                    if conversation_id:
                        folder1_conversations[conversation_id] = data
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {file_path}")

folder2_conversations = {}
if os.path.exists(folder2_path):
    for filename in os.listdir(folder2_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder2_path, filename)
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    conversation_id = data.get('conversation_id')
                    if conversation_id:
                        folder2_conversations[conversation_id] = data
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {file_path}")

shared_conversation_ids = set(folder1_conversations.keys()).intersection(folder2_conversations.keys())

print(f"Shared conversation IDs: {list(shared_conversation_ids)}")

