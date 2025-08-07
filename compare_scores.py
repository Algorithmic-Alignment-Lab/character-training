import typer
from typing import Optional, List
import os
import json
from collections import defaultdict

def get_score(data: dict) -> Optional[float]:
    """Extracts the primary score from a conversation's data."""
    if "evaluation_results" in data:
        for eval_name, eval_data in data["evaluation_results"].items():
            if isinstance(eval_data, dict):
                for key, value in eval_data.items():
                    if key.endswith("_score") and isinstance(value, (int, float)):
                        return value
    return None

def main(
    folder1: str = typer.Option(..., help="Path to the first folder of transcripts."),
    folder2: str = typer.Option(..., help="Path to the second folder of transcripts."),
    min_score: Optional[float] = typer.Option(None, "--min-score", "-s", help="Minimum score to consider a transcript."),
):
    """
    Compare conversation scores, filter by a minimum score, group by base name,
    and select the best-scoring file from each group.
    """
    all_files = []
    for folder_path in [folder1, folder2]:
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith('.json'):
                    all_files.append(os.path.join(folder_path, filename))

    scored_files = []
    for file_path in all_files:
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                score = get_score(data)
                if score is not None:
                    if min_score is None or score >= min_score:
                        scored_files.append({"path": file_path, "score": score, "data": data})
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {file_path}")

    grouped_files = defaultdict(list)
    for file_info in scored_files:
        conversation_id = file_info["data"].get("conversation_id")
        if conversation_id:
            grouped_files[conversation_id].append(file_info)

    best_files = []
    for group_key, files in grouped_files.items():
        if not files:
            continue
        best_file = max(files, key=lambda x: x['score'])
        best_files.append(best_file["path"])

    print("Best scoring files per conversation group:")
    for file_path in sorted(best_files):
        print(file_path)

if __name__ == "__main__":
    typer.run(main)
