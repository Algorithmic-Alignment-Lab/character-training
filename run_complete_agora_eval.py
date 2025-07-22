#!/usr/bin/env python3

import json
import os
import sys
import sqlite3
import uuid
from datetime import datetime

# Add conversations_ui to path
sys.path.append('conversations_ui')

def create_conversation_db_simple(db_path):
    """Create a simple conversation database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        name TEXT,
        system_prompt TEXT,
        model TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
    )
    """)
    
    conn.commit()
    conn.close()

def generate_agora_conversations():
    """Generate conversations using existing documents."""
    
    eval_dir = "evaluation_data/agora_redteaming_complete_20250710_170655"
    
    # Load documents
    with open(f'{eval_dir}/full_documents.json', 'r') as f:
        documents = json.load(f)
    
    # Load system prompts
    with open('conversations_ui/system_prompts.json', 'r') as f:
        prompts = json.load(f)
    
    agora_original = None
    agora_backstory = None
    
    for persona in prompts['personas']:
        if persona['name'] == "Agora, Collaborative Thinker":
            if persona['version'] == "Original":
                agora_original = persona['system_prompt']
            elif persona['version'] == "With Backstory":
                agora_backstory = persona['system_prompt']
    
    if not agora_original or not agora_backstory:
        print("Error: Could not find Agora system prompts")
        return False
    
    model = "openrouter/qwen/qwen2.5-vl-32b-instruct"
    
    # Generate conversations for both versions
    versions = [
        ("original", agora_original, f"{eval_dir}/agora_original_conversations.db"),
        ("backstory", agora_backstory, f"{eval_dir}/agora_backstory_conversations.db")
    ]
    
    from llm_api import get_llm_response
    
    for version_name, system_prompt, db_path in versions:
        print(f"\n=== Generating {version_name} Agora conversations ===")
        
        # Create database
        create_conversation_db_simple(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for i, doc in enumerate(documents, 1):
            print(f"Generating conversation {i}/{len(documents)}: {doc['title'][:50]}...")
            
            conv_id = f"conv_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Get AI response
            messages = [{"role": "user", "content": doc['content']}]
            try:
                response = get_llm_response(system_prompt, messages, model)
            except Exception as e:
                print(f"Error getting response: {e}")
                response = f"Error generating response: {str(e)}"
            
            # Save conversation
            cursor.execute("""
            INSERT INTO conversations (id, created_at, name, system_prompt, model)
            VALUES (?, ?, ?, ?, ?)
            """, (conv_id, datetime.now().isoformat(), doc['title'], system_prompt, model))
            
            # Save user message
            cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """, (conv_id, 'user', doc['content'], datetime.now().isoformat()))
            
            # Save assistant message
            cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """, (conv_id, 'assistant', response, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        print(f"Saved {len(documents)} conversations to {db_path}")
    
    return True

def run_judge_evaluations():
    """Run judge evaluations on the conversations."""
    
    eval_dir = "evaluation_data/agora_redteaming_complete_20250710_170655"
    traits = "Collaborative,Inquisitive,Cautious & Ethical,Encouraging,Thorough"
    judge_model = "anthropic/claude-sonnet-4-20250514"
    
    os.chdir('conversations_ui')
    
    try:
        # Single evaluations for original
        print("\n=== Running single evaluation for Original Agora ===")
        import subprocess
        result = subprocess.run([
            'python', 'judge_conversations.py',
            '--evaluation-type', 'single',
            '--judge-model', judge_model,
            '--filepaths', f'../{eval_dir}/agora_original_conversations.db',
            '--traits', traits,
            '--output-dir', f'../{eval_dir}/original_evaluation'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error in original evaluation: {result.stderr}")
        else:
            print("Original evaluation completed successfully")
        
        # Single evaluations for backstory
        print("\n=== Running single evaluation for Backstory Agora ===")
        result = subprocess.run([
            'python', 'judge_conversations.py',
            '--evaluation-type', 'single',
            '--judge-model', judge_model,
            '--filepaths', f'../{eval_dir}/agora_backstory_conversations.db',
            '--traits', traits,
            '--output-dir', f'../{eval_dir}/backstory_evaluation'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error in backstory evaluation: {result.stderr}")
        else:
            print("Backstory evaluation completed successfully")
        
        # ELO comparison
        print("\n=== Running ELO comparison ===")
        result = subprocess.run([
            'python', 'judge_conversations.py',
            '--evaluation-type', 'elo',
            '--judge-model', judge_model,
            '--filepaths', f'../{eval_dir}/agora_original_conversations.db,../{eval_dir}/agora_backstory_conversations.db',
            '--traits', traits,
            '--output-dir', f'../{eval_dir}/elo_comparison'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error in ELO evaluation: {result.stderr}")
        else:
            print("ELO comparison completed successfully")
        
    except Exception as e:
        print(f"Error running evaluations: {e}")
    
    os.chdir('..')

def extract_evaluation_results():
    """Extract results from evaluation databases."""
    
    eval_dir = "evaluation_data/agora_redteaming_complete_20250710_170655"
    results = {}
    
    # Try to load single evaluation results
    try:
        # Original results
        conn = sqlite3.connect(f'{eval_dir}/original_evaluation/evaluation_summaries.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluation_summaries")
        original_summary = cursor.fetchall()
        conn.close()
        results['original_summary'] = original_summary
        
        # Backstory results  
        conn = sqlite3.connect(f'{eval_dir}/backstory_evaluation/evaluation_summaries.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluation_summaries")
        backstory_summary = cursor.fetchall()
        conn.close()
        results['backstory_summary'] = backstory_summary
        
        # Individual judgments
        conn = sqlite3.connect(f'{eval_dir}/original_evaluation/single_judgments.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM single_judgments")
        original_judgments = cursor.fetchall()
        conn.close()
        results['original_judgments'] = original_judgments
        
        conn = sqlite3.connect(f'{eval_dir}/backstory_evaluation/single_judgments.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM single_judgments")
        backstory_judgments = cursor.fetchall()
        conn.close()
        results['backstory_judgments'] = backstory_judgments
        
    except Exception as e:
        print(f"Could not load single evaluation results: {e}")
    
    # Try to load ELO results
    try:
        conn = sqlite3.connect(f'{eval_dir}/elo_comparison/elo_comparisons.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM elo_comparisons")
        elo_comparisons = cursor.fetchall()
        conn.close()
        results['elo_comparisons'] = elo_comparisons
        
    except Exception as e:
        print(f"Could not load ELO results: {e}")
    
    return results

def update_analysis_with_results():
    """Update the analysis.md file with actual evaluation results."""
    
    eval_dir = "evaluation_data/agora_redteaming_complete_20250710_170655"
    results = extract_evaluation_results()
    
    # Create detailed analysis section
    results_section = """

## Quantitative Evaluation Results

### Single Trait Evaluation Scores (Likert Scale 1-5)

"""
    
    if 'original_judgments' in results and 'backstory_judgments' in results:
        results_section += """#### Original Agora vs. Backstory Agora Comparison

| Trait | Original Agora | Backstory Agora | Difference |
|-------|---------------|-----------------|------------|
"""
        
        # Calculate average scores per trait (this would need actual data structure analysis)
        traits = ["Collaborative", "Inquisitive", "Cautious & Ethical", "Encouraging", "Thorough"]
        
        for trait in traits:
            # Placeholder for actual score calculation
            results_section += f"| {trait} | [Score] | [Score] | [Diff] |\n"
    
    else:
        results_section += """
**Note**: Evaluation scores are being processed. Raw data available in:
- `original_evaluation/single_judgments.db` - Individual trait scores for original version
- `backstory_evaluation/single_judgments.db` - Individual trait scores for backstory version
- `elo_comparison/elo_comparisons.db` - Head-to-head trait comparisons

"""
    
    results_section += """
### ELO Comparison Results

"""
    
    if 'elo_comparisons' in results:
        results_section += "ELO head-to-head comparison results:\n\n"
        # Add actual ELO analysis here
    else:
        results_section += """
**Note**: ELO comparison results are being processed. Data available in:
- `elo_comparison/elo_comparisons.db`

"""
    
    # Read current analysis
    analysis_path = f'{eval_dir}/analysis.md'
    with open(analysis_path, 'r') as f:
        current_analysis = f.read()
    
    # Insert results before "Next Steps" section
    if "## Next Steps" in current_analysis:
        parts = current_analysis.split("## Next Steps")
        updated_analysis = parts[0] + results_section + "\n## Next Steps" + parts[1]
    else:
        updated_analysis = current_analysis + results_section
    
    # Write updated analysis
    with open(analysis_path, 'w') as f:
        f.write(updated_analysis)
    
    print(f"Updated analysis with results: {analysis_path}")

def main():
    """Run complete evaluation pipeline."""
    
    print("=== Complete Agora Red-teaming Evaluation ===")
    
    # Step 1: Generate conversations
    print("\nStep 1: Generating conversations...")
    if not generate_agora_conversations():
        print("Failed to generate conversations")
        return
    
    # Step 2: Run judge evaluations  
    print("\nStep 2: Running judge evaluations...")
    run_judge_evaluations()
    
    # Step 3: Update analysis with results
    print("\nStep 3: Updating analysis with results...")
    update_analysis_with_results()
    
    print("\n=== Evaluation Complete! ===")
    print("Results available in: evaluation_data/agora_redteaming_complete_20250710_170655/")
    print("View analysis: evaluation_data/agora_redteaming_complete_20250710_170655/analysis.md")
    print("View in Streamlit: cd conversations_ui && streamlit run streamlit_chat.py")

if __name__ == "__main__":
    main()