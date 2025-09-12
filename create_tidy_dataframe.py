"""
Creates a tidy DataFrame from conversation data in two folders and saves it to a CSV file.

This script loads conversations from two specified folders, finds the shared conversations
between them, and then loads associated judgments for these conversations. The judgments
are combined into a single tidy DataFrame where each row represents a single metric for a
single conversation.

The script filters out conversations where the 'overall_score' from the 'folder1' source
is below a specified minimum score. This minimum score can be adjusted via a command-line
argument.

Args:
    --folder1 (str): The path to the first folder containing conversation JSON files.
                     Defaults to 'folder1'.
    --folder2 (str): The path to the second folder containing conversation JSON files.
                     Defaults to 'folder2'.
    --min_score (float): The minimum overall score required for conversations from
                         folder1 to be included. Defaults to 8.0.

Example:
    python create_tidy_dataframe.py --folder1 /path/to/your/folder1 --folder2 /path/to/your/folder2 --min_score 7.5
"""


import json
import os
import pandas as pd
from pathlib import Path

from load_judgments import load_judgments

def load_conversations_from_folder(folder_path: str) -> dict:
    conversations = {}
    if not os.path.exists(folder_path):
        print(f"Warning: Directory not found at '{folder_path}'")
        return conversations
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    conversation_id = data.get('conversation_id')
                    if conversation_id:
                        conversations[conversation_id] = data
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {file_path}")
    return conversations

folder1_path = 'folder1'
folder2_path = 'folder2'

folder1_conversations = load_conversations_from_folder(folder1_path)
folder2_conversations = load_conversations_from_folder(folder2_path)

shared_conversation_ids = set(folder1_conversations.keys()).intersection(folder2_conversations.keys())

if not shared_conversation_ids:
    print("No shared conversation IDs found between the two folders.")
else:
    conversation_judgments = load_judgments('auto_eval_gen/results/transcripts/')
    teacher_judgments = load_judgments('auto_eval_gen/results_debiased/transcripts/')

    data_rows = []
    for conv_id in shared_conversation_ids:
        if conv_id in conversation_judgments:
            for metric, value in conversation_judgments[conv_id].items():
                data_rows.append({'conversation_id': conv_id, 'source': 'folder1', 'metric': metric, 'value': value})
        if conv_id in teacher_judgments:
            for metric, value in teacher_judgments[conv_id].items():
                data_rows.append({'conversation_id': conv_id, 'source': 'folder2', 'metric': metric, 'value': value})

    if not data_rows:
        print("No judgment data found for the shared conversations.")
    else:
        df = pd.DataFrame(data_rows)
        df.to_csv('tidy_data.csv', index=False)

        print("Tidy DataFrame created and saved to tidy_data.csv")
        print(df)

