import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# Load the data from the JSON file
with open('evals/results/eval_interviewer_v2_jasmine_vs_hates_customers_candidate_20250728_155308_20250728_181640/evaluation_summary.json', 'r') as f:
    data = json.load(f)

# Extract the evaluation results
results = data['results_per_conversation']

trait_scores_map = defaultdict(list)
for result in results:
    trait_adherence = result.get('evaluation_results', {}).get('traitadherence', {})
    if trait_adherence:
        for trait_score in trait_adherence.get('trait_scores', []):
            trait = trait_score.get('trait')
            score = trait_score.get('score')
            if trait and score is not None:
                trait_scores_map[trait].append(score)

if trait_scores_map:
    average_scores = {trait: np.mean(scores) for trait, scores in trait_scores_map.items()}

    # Sort traits for consistent plotting
    sorted_traits = sorted(average_scores.keys())
    scores = [average_scores[trait] for trait in sorted_traits]

    # Create the bar chart
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(sorted_traits, scores)

    ax.set_ylabel('Average Score')
    ax.set_title('Average Trait Scores')
    plt.xticks(rotation=45, ha='right')

    # Add the score labels to the bars
    for i, score in enumerate(scores):
        ax.text(i, score + 0.05, f'{score:.2f}', ha='center')

    plt.tight_layout()
    plt.savefig('output/trait_scores.png')

    print('Chart saved to output/trait_scores.png')
else:
    print("No trait scores were found.")
