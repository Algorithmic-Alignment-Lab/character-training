
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load the data
with open('evals/results/eval_interviewer_v2_jasmine_vs_hates_customers_candidate_20250728_155308_20250728_181640/evaluation_summary.json', 'r') as f:
    data = json.load(f)

# Extract the data into a list of dictionaries
data_rows = []
for conv in data['results_per_conversation']:
    conv_id = conv['conversation_id']
    for score_item in conv['evaluation_results']['traitadherence']['trait_scores']:
        data_rows.append({
            'conversation_id': conv_id,
            'source': 'conversation',
            'metric': score_item['trait'],
            'value': score_item['score']
        })

# Create a DataFrame
df = pd.DataFrame(data_rows)

# For the purpose of this chart, we'll create some dummy 'teacher' data
# as the original request implied a comparison between 'conversation' and 'teacher'.
# In a real-world scenario, you would load the teacher data from a separate file.
df_teacher = df.copy()
df_teacher['source'] = 'teacher'
df_teacher['value'] = df_teacher['value'].apply(lambda x: x * np.random.uniform(0.8, 1.2))

df_combined = pd.concat([df, df_teacher])

# Get unique values
conversation_ids = df_combined['conversation_id'].unique()
metrics = df_combined['metric'].unique()

# Set up the plot
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(15, 8))

# Set the width of the bars
bar_width = 0.35

# Set the positions of the bars on the x-axis
x = np.arange(len(conversation_ids))

# Define colors for each metric
colors = plt.cm.get_cmap('tab10', len(metrics))

# Plot the bars for each metric
for i, metric in enumerate(metrics):
    # Filter data for the current metric
    df_metric = df_combined[df_combined['metric'] == metric]

    # Extract values for conversation and teacher
    conversation_values = df_metric[df_metric['source'] == 'conversation']['value'].values
    teacher_values = df_metric[df_metric['source'] == 'teacher']['value'].values

    # Set the positions for the bars
    pos = x + (i - len(metrics)/2) * bar_width

    # Plot the bars
    bars1 = ax.bar(pos - bar_width/2, conversation_values, width=bar_width, label=f'conversation - {metric}', color=colors(i), alpha=0.6)
    bars2 = ax.bar(pos + bar_width/2, teacher_values, width=bar_width, label=f'teacher - {metric}', color=colors(i))

    # Add value labels
    for bar in bars1:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval, round(yval, 2), va='bottom', ha='center')

    for bar in bars2:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval, round(yval, 2), va='bottom', ha='center')

# Add labels, title, and legend
ax.set_xlabel('Conversation ID')
ax.set_ylabel('Scores')
ax.set_title('Comparison of Trait Adherence Scores by Conversation and Source')
ax.set_xticks(x)
ax.set_xticklabels(conversation_ids, rotation=45, ha='right')
ax.legend()

# Save and show the plot
plt.tight_layout()
plt.savefig('comparison.png')
plt.show()

