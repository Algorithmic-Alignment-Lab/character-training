
import json
import os
from glob import glob
import streamlit as st

def list_contexts(base_dir):
    """Lists all contexts in the given base directory."""
    contexts = []
    context_files = glob(os.path.join(base_dir, 'evals/synthetic_evaluation_data/contexts', '*.json'))
    for context_file in context_files:
        with open(context_file, 'r') as f:
            data = json.load(f)
            contexts.append({
                'id': data.get('id'),
                'timestamp': data.get('timestamp'),
                'path': context_file
            })
    return contexts

def list_conversations(base_dir):
    """Lists all conversations in the given base directory."""
    conversation_files = glob(os.path.join(base_dir, 'evals/synthetic_evaluation_data/conversations', '*.jsonl'))
    return [os.path.basename(f) for f in conversation_files]

def list_evals(base_dir):
    """Lists all evaluations in the given base directory."""
    evals = []
    eval_dirs = glob(os.path.join(base_dir, 'evals/results', 'eval_*'))
    for eval_dir in eval_dirs:
        summary_path = os.path.join(eval_dir, 'evaluation_summary.json')
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                summary = json.load(f)
                evals.append({
                    'id': os.path.basename(eval_dir),
                    'timestamp': summary.get('timestamp'),
                    'path': eval_dir,
                    'conversation_paths': summary.get('conversation_paths', []),
                    'summary_path': summary_path
                })
    return evals

def list_models(base_dir):
    """Lists all fine-tuned models in the given base directory."""
    models_file = os.path.join(base_dir, 'evals/finetuning/finetuned_models.json')
    if os.path.exists(models_file):
        with open(models_file, 'r') as f:
            return json.load(f)
    return []

@st.cache_data
def load_json(path):
    """Loads a JSON file from the given path."""
    with open(path, 'r') as f:
        return json.load(f)

