import os
import json
from pathlib import Path

def load_judgments(root: str) -> dict[str, dict]:
    """Walks `<root>/**/judgment.json`, loads JSON, and returns `{conversation_id: {metric_name: value, ...}}`."""
    judgments = {}
    root_path = Path(root)
    if not root_path.is_dir():
        print(f"Error: Root directory not found at '{root}'")
        return judgments
    judgment_files = list(root_path.rglob('judgment.json'))
    if not judgment_files:
        print(f"Warning: No 'judgment.json' files found in '{root}'")
        return judgments
    for path in judgment_files:
        with open(path, 'r') as f:
            try:
                content = f.read()
                if not content:
                    print(f"Warning: Empty judgment.json file at {path}")
                    continue
                data = json.loads(content)
                conversation_id = path.parent.name
                judgments[conversation_id] = data
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {path}")
            except Exception as e:
                print(f"An unexpected error occurred with file {path}: {e}")
    return judgments

if __name__ == '__main__':
    conversation_judgments = load_judgments('auto-eval-gen/results/transcripts/')
    teacher_judgments = load_judgments('auto-eval-gen/results_debiased/transcripts/')

    print("Conversation Judgments:")
    print(conversation_judgments)
    print("\nTeacher Judgments:")
    print(teacher_judgments)

