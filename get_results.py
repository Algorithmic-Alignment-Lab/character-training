
import os
import json

def find_evaluation_summaries(root_dir):
    """
    Finds all evaluation summaries in the given root directory.

    Args:
        root_dir: The root directory to search.

    Returns:
        A list of paths to the evaluation summaries.
    """
    evaluation_summaries = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if "evaluation_summary.json" in filename:
                evaluation_summaries.append(os.path.join(dirpath, filename))
    return evaluation_summaries

from collections import defaultdict

def process_trait_adherence(results_per_conversation):
    """
    Aggregates and calculates the mean trait adherence scores.

    Args:
        results_per_conversation: A list of conversation results.
    """
    trait_scores = defaultdict(list)
    for conversation in results_per_conversation:
        trait_adherence = conversation.get("evaluation_results", {}).get("traitadherence", {})
        if trait_adherence:
            for score_item in trait_adherence.get("trait_scores", []):
                trait = score_item.get("trait")
                score = score_item.get("score")
                if trait and isinstance(score, (int, float)):
                    trait_scores[trait].append(score)

    print("Trait Adherence Scores:")
    for trait, scores in sorted(trait_scores.items()):
        if scores:
            average_score = sum(scores) / len(scores)
            print(f"  {trait}: {average_score:.2f}")

if __name__ == "__main__":
    evaluation_summaries = find_evaluation_summaries("evals/results")
    scores = {
        "behavioralpredictability": [],
        "reasoningauthenticity": [],
        "engagementquality": [],
        "longtermconsistency": [],
        "contextretention": [],
    }
    all_conversations = []

    for summary_path in evaluation_summaries:
        with open(summary_path, "r") as f:
            data = json.load(f)
            all_conversations.extend(data["results_per_conversation"])
            for conversation in data["results_per_conversation"]:
                for eval_type, eval_data in conversation["evaluation_results"].items():
                    if eval_type in scores:
                        # Extract the specific score from the evaluation data
                        score_key = [key for key in eval_data.keys() if key.endswith("_score")][0]
                        scores[eval_type].append(eval_data[score_key])

    for eval_type, score_list in scores.items():
        if score_list:
            average_score = sum(score_list) / len(score_list)
            print(f"Average score for {eval_type}: {average_score:.2f}")
    
    process_trait_adherence(all_conversations)

