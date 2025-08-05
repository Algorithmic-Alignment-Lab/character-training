
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load the data
df = pd.read_csv('tidy_data.csv')

# Set up the plot
plt.style.use('seaborn-v0_8-whitegrid')

# Get unique values
conversation_ids = df['conversation_id'].unique()
metrics = df['metric'].unique()

# Set the width of the bars
bar_width = 0.35

# Set the positions of the bars on the x-axis
r1 = np.arange(len(metrics))
r2 = [x + bar_width for x in r1]

# Create the plot
fig, ax = plt.subplots(figsize=(12, 8))

# Loop through each conversation ID to create grouped bars
for i, conv_id in enumerate(conversation_ids):
    # Filter data for the current conversation
    df_conv = df[df['conversation_id'] == conv_id]

    # Extract values for conversation and teacher
    conversation_values = df_conv[df_conv['source'] == 'conversation']['value'].values
    teacher_values = df_conv[df_conv['source'] == 'teacher']['value'].values

    # Set the positions for the groups
    group_positions = np.arange(len(metrics)) + i * (len(metrics) + 2) * bar_width

    # Plot the bars
    ax.bar(group_positions - bar_width/2, conversation_values, width=bar_width, label=f'{conv_id} - conversation')
    ax.bar(group_positions + bar_width/2, teacher_values, width=bar_width, label=f'{conv_id} - teacher')

# Add labels, title, and legend
ax.set_xlabel('Metrics')
ax.set_ylabel('Scores')
ax.set_title('Comparison of Scores by Conversation and Source')
ax.set_xticks(np.arange(len(metrics)))
ax.set_xticklabels(metrics)
ax.legend()

# Save and show the plot
plt.savefig('comparison.png')

