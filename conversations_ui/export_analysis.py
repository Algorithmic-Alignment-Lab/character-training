import sqlite3
import pandas as pd
import json
import os
import argparse

# --- Configuration ---
PROMPTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'system_prompts.json')

def get_persona_name_map():
    """Creates a mapping from system prompt content to persona name."""
    try:
        with open(PROMPTS_PATH, 'r') as f:
            prompts = json.load(f)
        return {v: k for k, v in prompts.items()}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading system prompts file: {e}")
        return {}

def export_analysis_to_csv(database_path: str, output_path: str):
    """Exports character analysis data from the database to a CSV file."""
    if not os.path.exists(database_path):
        print(f"Database not found at {database_path}")
        return

    try:
        with sqlite3.connect(database_path) as conn:
            # Query the necessary data using a JOIN
            query = """
            SELECT 
                ca.conversation_id,
                c.system_prompt,
                ca.message_index,
                m.content as ai_message,
                ca.is_in_character,
                ca.failure_type,
                ca.consistency_score,
                ca.trait_evaluations,
                ca.analysis,
                ca.interesting_moment
            FROM character_analysis ca
            JOIN conversations c ON ca.conversation_id = c.id
            JOIN messages m ON ca.conversation_id = m.conversation_id AND ca.message_index = m.message_index
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
    processed_df.to_csv(output_path, index=False)
    print(f"Successfully exported analysis to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export character analysis data to CSV.")
    parser.add_argument("--database-file", default="conversations.db", help="Path to the SQLite database file.")
    parser.add_argument("--output-csv", required=True, help="Path to the output CSV file.")
    args = parser.parse_args()

    export_analysis_to_csv(args.database_file, args.output_csv)
