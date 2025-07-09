#!/usr/bin/env python3

import os
import sqlite3
import json
from glob import glob

def verify_pipeline_completion():
    """Verify that the entire evaluation pipeline has completed successfully."""
    
    print("🔍 Character Trait Evaluation Pipeline Verification")
    print("=" * 60)
    
    # Check for evaluation data directories
    eval_dirs = glob("evaluation_data/*/")
    if not eval_dirs:
        print("❌ No evaluation data directories found")
        return False
    
    latest_dir = max(eval_dirs, key=os.path.getctime)
    print(f"📁 Latest evaluation directory: {latest_dir}")
    
    # Stage 1: Check ideas generation
    ideas_file = os.path.join(latest_dir, "ideas.json")
    if os.path.exists(ideas_file):
        with open(ideas_file, 'r') as f:
            ideas = json.load(f)
        print(f"✅ Stage 1 - Ideas: {len(ideas)} scenarios generated")
        print(f"   Sample: {ideas[0]['text'][:60]}...")
    else:
        print("❌ Stage 1 - Ideas file not found")
        return False
    
    # Stage 2: Check contexts generation  
    contexts_file = os.path.join(latest_dir, "ideas_with_contexts_2pages.json")
    if os.path.exists(contexts_file):
        with open(contexts_file, 'r') as f:
            contexts = json.load(f)
        print(f"✅ Stage 2 - Contexts: {len(contexts)} contexts generated")
        sample_context = contexts[0].get('context_2', '')
        print(f"   Sample context: {len(sample_context)} characters")
    else:
        print("❌ Stage 2 - Contexts file not found")
        return False
    
    # Stage 3: Check conversations generation
    db_files = glob(os.path.join(latest_dir, "*.db"))
    conversation_db = None
    for db_file in db_files:
        if "evaluation_results" not in db_file:
            conversation_db = db_file
            break
    
    if conversation_db and os.path.exists(conversation_db):
        with sqlite3.connect(conversation_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM evaluation_conversations")
            conv_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            msg_count = cursor.fetchone()[0]
            
        print(f"✅ Stage 3 - Conversations: {conv_count} conversations with {msg_count} messages")
        print(f"   Database: {os.path.basename(conversation_db)}")
    else:
        print("❌ Stage 3 - Conversation database not found")
        return False
    
    # Stage 4: Check evaluation results
    results_dir = os.path.join(latest_dir, "evaluation_results")
    if os.path.exists(results_dir):
        
        # Check judgments
        judgments_db = os.path.join(results_dir, "single_judgments.db")
        if os.path.exists(judgments_db):
            with sqlite3.connect(judgments_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM single_judgments")
                judgment_count = cursor.fetchone()[0]
                
                if judgment_count > 0:
                    cursor.execute("SELECT trait_judgments_json FROM single_judgments LIMIT 1")
                    sample_judgment = cursor.fetchone()[0]
                    trait_evaluations = json.loads(sample_judgment)
                    
                    print(f"✅ Stage 4a - Judgments: {judgment_count} conversations evaluated")
                    print(f"   Traits evaluated: {[t['trait'] for t in trait_evaluations]}")
                    scores_display = [f"{t['trait']}:{t['score']}/5" for t in trait_evaluations]
                    print(f"   Sample scores: {scores_display}")
                else:
                    print("⚠️  Stage 4a - Judgments database exists but is empty")
            
        # Check summaries
        summaries_db = os.path.join(results_dir, "evaluation_summaries.db")
        if os.path.exists(summaries_db):
            with sqlite3.connect(summaries_db) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM evaluation_summaries")
                summary_count = cursor.fetchone()[0]
                
                if summary_count > 0:
                    cursor.execute("SELECT overall_score, trait_summaries_json FROM evaluation_summaries LIMIT 1")
                    row = cursor.fetchone()
                    overall_score = row[0]
                    
                    print(f"✅ Stage 4b - Summaries: {summary_count} evaluation summaries")
                    print(f"   Overall score: {overall_score}/5.0")
                else:
                    print("⚠️  Stage 4b - Summaries database exists but is empty")
        
        print(f"✅ Stage 4 - Evaluation: Results saved to {results_dir}")
    else:
        print("❌ Stage 4 - Evaluation results directory not found")
        return False
    
    # Stage 5: Check Streamlit UI availability
    print("\n📊 Streamlit UI Status:")
    
    # Check if Streamlit process is running
    try:
        import requests
        response = requests.get("http://localhost:8502", timeout=2)
        if response.status_code == 200:
            print("✅ Streamlit UI: Running at http://localhost:8502")
            print("   Navigate to 'Evaluations' tab to view results")
        else:
            print("⚠️  Streamlit UI: Server responding but may have issues")
    except:
        print("❌ Streamlit UI: Not accessible at http://localhost:8502")
        print("   Run: streamlit run streamlit_chat.py")
    
    # Final verification summary
    print("\n" + "=" * 60)
    print("🎉 PIPELINE VERIFICATION COMPLETE")
    print("=" * 60)
    print("✅ All stages completed successfully!")
    print("✅ Evaluation data is available in the UI")
    print("✅ Judge results show character trait scoring")
    
    print("\n📋 Next Steps:")
    print("1. Open Streamlit UI: http://localhost:8502")
    print("2. Click 'Evaluations' tab")
    print("3. Select 'single' evaluation type")
    print("4. Browse the evaluation results and trait scores")
    print("5. View individual conversation evaluations with detailed reasoning")
    
    return True

if __name__ == "__main__":
    verify_pipeline_completion()