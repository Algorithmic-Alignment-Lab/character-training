
import pandas as pd
import numpy as np

# Define metrics and conversation IDs
metrics = ['metric1', 'metric2', 'metric3']
conversation_ids = ['conv1', 'conv2', 'conv3']
sources = ['conversation', 'teacher']

# Create a list of dictionaries
data = []
for conv_id in conversation_ids:
    for metric in metrics:
        for source in sources:
            data.append({
                'conversation_id': conv_id,
                'metric': metric,
                'source': source,
                'value': np.random.rand()
            })

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv('tidy_data.csv', index=False)

print("Dummy data created and saved to tidy_data.csv")

