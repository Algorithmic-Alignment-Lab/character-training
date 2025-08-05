
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Function to load judgments
def load_judgments(root: str) -> dict[str, dict]:
    judgments = {}
    for path in Path(root).rglob('judgment.json'):
        with open(path, 'r') as f:
            try:
                data = json.load(f)
                # Find the parent directory that is a number (the conversation id)
                conv_id = path.parent.name
                judgments[conv_id] = data
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {path}")
    return judgments

# Load the judgments
conversation_judgments = load_judgments('auto-eval-gen/results/transcripts/agora_inquisitiveness-example/20250804-114032')
teacher_judgments = load_judgments('auto-eval-gen/results/transcripts/agora_inquisitiveness-example/20250804-114032-teacher')

# Create a list of dictionaries
data_rows = []
for conv_id, judgment in conversation_judgments.items():
    data_rows.append({
        'conversation_id': conv_id,
        'source': 'conversation',
        'metric': 'eval_success_score',
        'value': judgment.get('eval_success_score', 0)
    })

for conv_id, judgment in teacher_judgments.items():
    data_rows.append({
        'conversation_id': conv_id,
        'source': 'teacher',
        'metric': 'eval_success_score',
        'value': judgment.get('eval_success_score', 0)
    })


# Create a DataFrame
df = pd.DataFrame(data_rows)

# Get unique values
conversation_ids = df['conversation_id'].unique()

# Set up the plot
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(15, 8))

# Set the width of the bars
bar_width = 0.35

# Set the positions of the bars on the x-axis
x = np.arange(len(conversation_ids))

# Plot the bars for each source
conversation_values = df[df['source'] == 'conversation']['value'].values
teacher_values = df[df['source'] == 'teacher']['value'].values

ax.bar(x - bar_width/2, conversation_values, width=bar_width, label='conversation')
ax.bar(x + bar_width/2, teacher_values, width=bar_width, label='teacher')

# Add value labels
for i, (conv_val, teach_val) in enumerate(zip(conversation_values, teacher_values)):
    ax.text(i - bar_width/2, conv_val, round(conv_val, 2), va='bottom', ha='center')
    ax.text(i + bar_width/2, teach_val, round(teach_val, 2), va='bottom', ha='center')

# Add labels, title, and legend
ax.set_xlabel('Conversation ID')
ax.set_ylabel('Eval Success Score')
ax.set_title('Comparison of Eval Success Scores by Source')
ax.set_xticks(x)
ax.set_xticklabels(conversation_ids, rotation=45, ha='right')
ax.legend()

# Save the plot
plt.tight_layout()
plt.savefig('comparison.png')

