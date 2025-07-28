import streamlit as st
import json
import os
import pandas as pd
from pathlib import Path
import sys
import numpy as np

def find_project_root(start_path, marker_file=".git"):
    """Find the project root by looking for a marker file."""
    current_path = Path(start_path).resolve()
    while current_path != current_path.parent:
        if (current_path / marker_file).exists():
            return current_path
        current_path = current_path.parent
    return None

def extract_score(eval_name: str, result: dict) -> float:
    """Extracts a numerical score from a result dictionary, handling various structures."""
    if not isinstance(result, dict):
        return np.nan

    # Trait Adherence: average of trait scores
    if eval_name == "trait_adherence" and "trait_scores" in result and result["trait_scores"]:
        scores = [s.get('score') for s in result["trait_scores"]]
        valid_scores = [s for s in scores if s is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else np.nan

    # Other evaluators with specific score keys
    score_keys = [
        "predictability_score", "engagement_score", "consistency_score",
        "retention_score", "authenticity_score", "score"
    ]
    for key in score_keys:
        if key in result and result[key] is not None:
            return float(result[key])
            
    return np.nan

def calculate_aggregate_metrics(results_per_conversation: list) -> pd.DataFrame:
    """Calculates and summarizes aggregate metrics from all conversations."""
    if not results_per_conversation:
        return pd.DataFrame()

    all_scores = {}
    for convo in results_per_conversation:
        eval_results = convo.get("evaluation_results", {})
        for eval_name, result in eval_results.items():
            if eval_name not in all_scores:
                all_scores[eval_name] = []
            
            score = extract_score(eval_name, result)
            if not np.isnan(score):
                all_scores[eval_name].append(score)

    summary_data = []
    for eval_name, scores in all_scores.items():
        if scores:
            avg_score = np.mean(scores)
            summary_data.append({
                "Evaluation": eval_name.replace('_', ' ').title(),
                "Average Score": f"{avg_score:.2f}/7",
                "Conversations Evaluated": len(scores)
            })
        else:
            summary_data.append({
                "Evaluation": eval_name.replace('_', ' ').title(),
                "Average Score": "N/A",
                "Conversations Evaluated": 0
            })
            
    if not summary_data:
        return pd.DataFrame()

    return pd.DataFrame(summary_data).set_index("Evaluation")

def main(headless=False):
    """
    The main function for the Streamlit evaluation dashboard.
    If headless is True, it runs a quick check and exits.
    """
    project_root = find_project_root(__file__)
    if not project_root:
        st.error("Could not find the project root. Make sure you are running this from within the project.")
        return

    st.set_page_config(layout="wide", page_title="Character Evaluation Dashboard")
    st.title("Character Evaluation Dashboard")

    results_dir = project_root / "evals" / "results"
    if not results_dir.exists():
        st.error(f"Results directory not found at: {results_dir}")
        return

    # --- File Selector ---
    run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime, reverse=True)
    run_options = {d.name: d for d in run_dirs}
    selected_run_name = st.selectbox("Select Evaluation Run", options=list(run_options.keys()))

    if not selected_run_name:
        st.warning("No evaluation runs found.")
        return

    selected_run_dir = run_options[selected_run_name]
    summary_file = selected_run_dir / "evaluation_summary.json"

    if not summary_file.exists():
        st.error(f"evaluation_summary.json not found in {selected_run_dir}")
        return

    # --- Load Data ---
    try:
        with open(summary_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        st.error("Failed to parse the summary JSON file.")
        return
    
    if headless:
        print("Headless test successful: Data loaded.")
        return

    # --- Display Run Info ---
    st.sidebar.title("Run Information")
    run_info = data.get("run_info", {})
    for key, value in run_info.items():
        st.sidebar.info(f"**{key.replace('_', ' ').title()}:** {value}")

    # --- Aggregate Summary View ---
    st.header("Aggregate Results")
    st.markdown("This table shows the average scores for each evaluation metric across all conversations in this run.")
    
    results_per_conversation = data.get("results_per_conversation", [])
    aggregate_df = calculate_aggregate_metrics(results_per_conversation)
    
    if aggregate_df.empty:
        st.warning("No evaluation results found to aggregate.")
    else:
        st.table(aggregate_df)

    # --- Detailed Per-Conversation View ---
    st.header("Detailed Conversation Analysis")
    
    if not results_per_conversation:
        st.warning("No individual conversation results to display.")
        return

    conversation_ids = [convo.get("conversation_id", f"Conversation {i+1}") for i, convo in enumerate(results_per_conversation)]
    selected_convo_id = st.selectbox("Select a conversation to inspect:", options=conversation_ids)
    
    # Find the selected conversation data
    selected_convo_data = next((c for c in results_per_conversation if c.get("conversation_id") == selected_convo_id), None)

    if not selected_convo_data:
        st.error("Could not find the selected conversation data.")
        return

    # --- Display Detailed Results for the Selected Conversation ---
    eval_results = selected_convo_data.get("evaluation_results", {})
    
    # Display summary table for the selected conversation
    st.subheader(f"Evaluation Scores for: {selected_convo_id}")
    summary_data = []
    for eval_name, result in eval_results.items():
        score_val = extract_score(eval_name, result)
        score_str = f"{score_val:.2f}/7" if not np.isnan(score_val) else "N/A"
        reasoning = result.get("reasoning", "No reasoning provided.") if isinstance(result, dict) else str(result)
        
        summary_data.append({
            "Evaluation": eval_name.replace('_', ' ').title(),
            "Score": score_str,
            "Summary": reasoning.split('.')[0]
        })
    st.table(pd.DataFrame(summary_data).set_index("Evaluation"))


    # --- Detailed Drill-Downs in Tabs ---
    st.subheader("Detailed Analysis")
    tab_titles = ["Conversation Log"] + [name.replace('_', ' ').title() for name in eval_results.keys()]
    tabs = st.tabs(tab_titles)

    # Conversation Log Tab
    with tabs[0]:
        st.markdown("#### Full Conversation")
        for message in selected_convo_data.get("conversation_log", []):
            speaker = message.get("speaker", "Unknown")
            text = message.get("message", "")
            # Simple display for now, can be enhanced
            with st.chat_message("user" if speaker == "User" else "assistant"):
                st.write(text)

    # Evaluator Tabs
    for i, (eval_name, eval_result) in enumerate(eval_results.items()):
        with tabs[i+1]:
            if isinstance(eval_result, dict):
                st.markdown(f"#### Reasoning")
                st.info(eval_result.get("reasoning", "No reasoning provided."))
                
                if eval_name == "trait_adherence" and "trait_scores" in eval_result:
                    st.markdown("#### Trait Scores")
                    st.table(pd.DataFrame(eval_result["trait_scores"]))
                else:
                    st.markdown("#### Full JSON Output")
                    st.json(eval_result)
            else:
                st.error("An error occurred during this evaluation:")
                st.code(str(eval_result))


if __name__ == '__main__':
    if "--headless" in sys.argv:
        main(headless=True)
    else:
        main()