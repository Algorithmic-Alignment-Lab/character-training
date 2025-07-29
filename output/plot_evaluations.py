import json
import matplotlib.pyplot as plt
import numpy as np

# Load the data from the JSON file
with open('evals/results/eval_interviewer_v2_jasmine_vs_hates_customers_candidate_20250728_155308_20250728_181640/evaluation_summary.json', 'r') as f:
    data = json.load(f)

# Extract the evaluation results
results = data['results_per_conversation']

# Calculate the average scores for each trait
trait_scores = {}
for result in results:
    for trait, score in result['trait_scores'].items():
        if trait not in trait_scores:
            trait_scores[trait] = []
        trait_scores[trait].append(score)

average_scores = {trait: np.mean(scores) for trait, scores in trait_scores.items()}

# Create the bar chart
plt.style.use('ggplot')
fig, ax = plt.subplots(figsize=(10, 6))

traits = list(average_scores.keys())
scores = list(average_scores.values())

ax.bar(traits, scores)

ax.set_ylabel('Average Score')
ax.set_title('Average Trait Scores')
ax.set_xticklabels(traits, rotation=45, ha='right')

# Add the score labels to the bars
for i, score in enumerate(scores):
    ax.text(i, score + 0.1, f'{score:.2f}', ha='center')

plt.tight_layout()
plt.savefig('output/trait_scores.png')

print('Chart saved to output/trait_scores.png')

import json
import matplotlib.pyplot as plt
import numpy as np

# Load the data from the JSON file
with open('evals/results/eval_interviewer_v2_jasmine_vs_hates_customers_candidate_20250728_155308_20250728_181640/evaluation_summary.json', 'r') as f:
    data = json.load(f)

# Extract the evaluation results
results = data['results_per_conversation']

# Calculate the average scores for each evaluation
evaluation_scores = {}
for result in results:
    for eval_name, eval_data in result['evaluation_results'].items():
        if eval_name not in evaluation_scores:
            evaluation_scores[eval_name] = []
        if 'score' in eval_data:
            evaluation_scores[eval_name].append(eval_data['score'])
        elif 'predictability_score' in eval_data:
            evaluation_scores[eval_name].append(eval_data['predictability_score'])
        elif 'authenticity_score' in eval_data:
            evaluation_scores[eval_name].append(eval_data['authenticity_score'])
        elif 'engagement_score' in eval_data:
            evaluation_scores[eval_name].append(eval_data['engagement_score'])
        elif 'consistency_score' in eval_data:
            evaluation_scores[eval_name].append(eval_data['consistency_score'])
        elif 'retention_score' in eval_data:
            evaluation_scores[eval_name].append(eval_data['retention_score'])


average_scores = {name: np.mean(scores) for name, scores in evaluation_scores.items()}

# Create the bar chart
plt.style.use('ggplot')
fig, ax = plt.subplots(figsize=(10, 6))

evaluations = list(average_scores.keys())
scores = list(average_scores.values())

ax.bar(evaluations, scores)

ax.set_ylabel('Average Score')
ax.set_title('Average Evaluation Scores')
ax.set_xticklabels(evaluations, rotation=45, ha='right')

# Add the score labels to the bars
for i, score in enumerate(scores):
    ax.text(i, score + 0.1, f'{score:.2f}', ha='center')

plt.tight_layout()
plt.savefig('output/evaluation_scores.png')

print('Chart saved to output/evaluation_scores.png')
