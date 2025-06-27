import sqlite3
import pandas as pd
import json
import os

# --- Configuration ---
DATABASE_PATH = os.path.join('conversations_ui', 'conversations.db')
PROMPTS_PATH = os.path.join('conversations_ui', 'system_prompts.json')
OUTPUT_PATH = os.path.join('conversations_ui', 'failure_modes.csv')

def get_persona_name_map():
    """Creates a mapping from system prompt content to persona name."""
    try:
        with open(PROMPTS_PATH, 'r') as f:
            prompts = json.load(f)
        return {v: k for k, v in prompts.items()}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading system prompts file: {e}")
        return {}

def export_analysis_to_csv():
    """Exports character analysis data from the database to a CSV file."""
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        return

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            # Query the necessary data using a JOIN
            query = """
            SELECT 
                ca.conversation_id,
                c.system_prompt,
                ca.message_index,
                ca.is_in_character,
                ca.failure_type,
                ca.consistency_score,
                ca.trait_evaluations,
                ca.analysis,
                ca.interesting_moment
            FROM character_analysis ca
            JOIN conversations c ON ca.conversation_id = c.id
            """
            df = pd.read_sql_query(query, conn)
    except pd.io.sql.DatabaseError as e:
        print(f"Error querying the database: {e}")
        return

    if df.empty:
        print("No analysis data found in the database.")
        return

    # Map system prompt to persona name
    persona_map = get_persona_name_map()
    if not persona_map:
        print("Could not create persona map. Aborting.")
        return
        
    df['ai_persona'] = df['system_prompt'].map(persona_map)

    # Process trait evaluations
    rows = []
    for _, row in df.iterrows():
        try:
            evals = json.loads(row['trait_evaluations'])
            if isinstance(evals, list):
                for e in evals:
                    new_row = row.to_dict()
                    new_row['trait'] = e.get('trait')
                    new_row['trait_score'] = e.get('score')
                    new_row['trait_reasoning'] = e.get('reasoning')
                    rows.append(new_row)
            else:
                 rows.append(row.to_dict()) # Keep original if no traits
        except (json.JSONDecodeError, TypeError):
            rows.append(row.to_dict()) # Keep original if error

    if not rows:
        print("No data to process after handling trait evaluations.")
        return

    processed_df = pd.DataFrame(rows)
    
    # Clean up columns
    processed_df.drop(columns=['trait_evaluations', 'system_prompt'], inplace=True)

    # Save to CSV
    processed_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Successfully exported analysis to {OUTPUT_PATH}")

if __name__ == "__main__":
    export_analysis_to_csv()
