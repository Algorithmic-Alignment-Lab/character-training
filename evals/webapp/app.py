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

def extract_score(eval_name: str, result: dict) -> tuple[float, str]:
    """Extracts a numerical score from a result dictionary, handling various structures."""
    if not isinstance(result, dict):
        return np.nan, str(result)

    # Trait Adherence: average of trait scores and concatenated reasoning
    if eval_name == "trait_adherence" and "trait_scores" in result and result["trait_scores"]:
        scores = [s.get('score') for s in result["trait_scores"]]
        valid_scores = [s for s in scores if s is not None]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else np.nan
        
        reasoning_parts = [s.get('reasoning', '') for s in result["trait_scores"]]
        concatenated_reasoning = '\n'.join(filter(None, reasoning_parts))
        if not concatenated_reasoning:
            concatenated_reasoning = result.get("reasoning", "No reasoning provided.")
        return avg_score, concatenated_reasoning

    # Other evaluators with specific score keys
    score_keys = [
        "predictability_score", "engagement_score", "consistency_score",
        "retention_score", "authenticity_score", "score"
    ]
    score = np.nan
    for key in score_keys:
        if key in result and result[key] is not None:
            score = float(result[key])
            break

    reasoning = result.get("reasoning", "No reasoning provided.")
    return score, reasoning

def calculate_aggregate_metrics(results_per_conversation: list) -> pd.DataFrame:
    """Calculates and summarizes aggregate metrics from all conversations."""
    if not results_per_conversation:
        return pd.DataFrame()

    all_scores = {}
    for convo in results_per_conversation:
        eval_results = convo.get("evaluation_results", {})
        for eval_name, result in eval_results.items():
            # Normalize eval_name to handle potential case inconsistencies
            normalized_eval_name = eval_name.lower()
            if normalized_eval_name not in all_scores:
                all_scores[normalized_eval_name] = []
            
            if normalized_eval_name == "traitadherence":
                if "trait_scores" in result and result["trait_scores"]:
                    scores = [s.get('score') for s in result["trait_scores"]]
                    valid_scores = [s for s in scores if s is not None]
                    all_scores[normalized_eval_name].extend(valid_scores) # Use extend to gather all trait scores
            else:
                score, _ = extract_score(normalized_eval_name, result)
                if not np.isnan(score):
                    all_scores[normalized_eval_name].append(score)

    summary_data = []
    for eval_name, scores in all_scores.items():
        if scores:
            avg_score = np.mean(scores)
            num_evaluated = len(results_per_conversation) if eval_name == "traitadherence" else len(scores)
            summary_data.append({
                "Evaluation": eval_name.replace('_', ' ').title(),
                "Average Score": f"{avg_score:.2f}/7",
                "Conversations Evaluated": num_evaluated
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

def get_convo_display_name(convo: dict) -> str:
    """Creates a display name for a conversation, including a timestamp if available."""
    # Prioritize 'timestamp', then 'start_time'
    timestamp = convo.get('timestamp', convo.get('start_time'))
    convo_id = convo.get('conversation_id', 'Unknown Conversation')
    
    if timestamp:
        # Assuming timestamp is in a readable format or can be converted.
        # For simplicity, we'll just display it as is.
        return f"{timestamp} - {convo_id}"
    return convo_id

def display_context_file(context_data: list):
    """Custom function to display context files as requested."""
    for i, context_item in enumerate(context_data):
        st.markdown(f"---_Item {i+1}_---")
        if isinstance(context_item, dict):
            # Display starting_prompt by default
            if "starting_prompt" in context_item:
                with st.container():
                    st.subheader("Starting Prompt")
                    st.markdown(context_item["starting_prompt"])
            
            # Put supporting documents in a single expander
            if "supporting_documents" in context_item and context_item["supporting_documents"]:
                with st.expander("View Supporting Documents"):
                    for doc in context_item["supporting_documents"]:
                        if isinstance(doc, dict):
                            for key, value in doc.items():
                                st.text_area(key, value, height=150, disabled=True)
                        else:
                            st.text(str(doc))
            
            # Display any other keys
            for key, value in context_item.items():
                if key not in ["starting_prompt", "supporting_documents"]:
                    st.markdown(f"**{key}:**")
                    st.json(value)
        else:
            st.text(str(context_item))

def main():
    """
    The main function for the Streamlit evaluation dashboard.
    """
    st.set_page_config(layout="wide", page_title="Character Evaluation Dashboard")
    st.title("Character Evaluation Dashboard")

    project_root = find_project_root(__file__)
    if not project_root:
        st.error("Could not find the project root. Make sure you are running this from within the project.")
        return

    # Top-level navigation
    page = st.sidebar.radio("Navigation", ["Contexts", "Conversations", "Evaluation Results", "Finetuning Results"])

    if page == "Contexts":
        contexts_page(project_root)
    elif page == "Conversations":
        conversations_page(project_root)
    elif page == "Evaluation Results":
        evals_page(project_root)
    elif page == "Finetuning Results":
        finetuning_page(project_root)

def contexts_page(project_root):
    st.header("Contexts")
    st.sidebar.title("Context Selection")
    contexts_dir = project_root / "evals" / "synthetic_evaluation_data" / "contexts"
    if contexts_dir.exists():
        context_files = sorted([f for f in contexts_dir.iterdir() if f.is_file() and f.suffix == '.json'], key=os.path.getmtime, reverse=True)
        if context_files:
            selected_context_file = st.sidebar.selectbox("Select a context file", context_files, format_func=lambda f: f.name, key="context_selector")
            if selected_context_file:
                with open(selected_context_file, 'r') as f:
                    context_data = json.load(f)
                display_context_file(context_data)
        else:
            st.warning("No context files found.")
    else:
        st.error(f"Contexts directory not found at: {contexts_dir}")

def conversations_page(project_root):
    st.header("Conversations")
    st.sidebar.title("Conversation Selection")
    conversations_dir = project_root / "evals" / "synthetic_evaluation_data" / "conversations"
    if conversations_dir.exists():
        conversation_files = sorted([f for f in conversations_dir.iterdir() if f.is_file() and f.suffix == '.jsonl'], key=os.path.getmtime, reverse=True)
        if conversation_files:
            selected_convo_file = st.sidebar.selectbox("Select a conversation file", conversation_files, format_func=lambda f: f.name, key="conversation_selector")
            if selected_convo_file:
                with open(selected_convo_file, 'r') as f:
                    for line in f:
                        convo = json.loads(line)
                        with st.expander(f"Conversation ID: {convo.get('conversation_id')}"):
                            for message in convo.get("conversation_log", []):
                                speaker = message.get("role", "Unknown") # Use role for speaker
                                text = message.get("content", "")
                                with st.chat_message(speaker):
                                    st.markdown(text)
        else:
            st.warning("No conversation files found.")
    else:
        st.error(f"Conversations directory not found at: {conversations_dir}")

def evals_page(project_root):
    st.header("Evaluation Results")
    st.sidebar.title("Eval Selection")
    results_dir = project_root / "evals" / "results"
    if not results_dir.exists():
        st.error(f"Results directory not found at: {results_dir}")
        return

    run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime, reverse=True)
    if not run_dirs:
        st.warning("No evaluation runs found.")
        return

    run_options = {d.name: d for d in run_dirs}
    selected_run_name = st.sidebar.selectbox("Select Evaluation Run", options=list(run_options.keys()), key="eval_run_selector")

    if selected_run_name:
        summary_file = run_options[selected_run_name] / "evaluation_summary.json"
        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    data = json.load(f)
                
                metadata = data.get("run_info", None)
                if metadata:
                    st.sidebar.subheader("Run Metadata")
                    st.sidebar.json(metadata)

                results_per_conversation = data.get("results_per_conversation", [])

                st.subheader("Aggregate Results")
                aggregate_df = calculate_aggregate_metrics(results_per_conversation)
                if not aggregate_df.empty:
                    st.dataframe(aggregate_df)
                else:
                    st.warning("No evaluation results found to aggregate.")

                st.subheader("Conversation Selector")
                selected_convo_data = st.selectbox(
                    'Select a Conversation to Drill Down',
                    [None] + results_per_conversation,
                    format_func=lambda c: "None" if c is None else get_convo_display_name(c),
                    key="convo_drilldown_selector"
                )
                
                if selected_convo_data:
                    st.divider()
                    st.subheader("Conversation Details")
                    detail_tabs = st.tabs(["Evaluation Scores", "Conversation Log", "Context"])

                    with detail_tabs[0]:
                        eval_results = selected_convo_data.get("evaluation_results", {})
                        if eval_results:
                            for eval_name, result in eval_results.items():
                                st.markdown(f"#### {eval_name.replace('_', ' ').title()}")
                                score, reasoning = extract_score(eval_name, result)
                                st.metric(label="Average Score" if eval_name.lower() == 'traitadherence' else "Score", value=f"{score:.2f}/7" if not np.isnan(score) else "N/A")
                                
                                if reasoning:
                                    st.text_area("Reasoning", reasoning, height=120, disabled=True, key=f"reasoning_{eval_name}_{selected_convo_data['conversation_id']}")
                                
                                if eval_name.lower() == "traitadherence" and "trait_scores" in result:
                                    with st.expander("Individual Trait Scores"):
                                        for trait in result["trait_scores"]:
                                            st.markdown(f"**{trait['trait']}:** {trait['score']}/7")
                                            st.text_area("Trait Reasoning", trait['reasoning'], height=100, disabled=True, key=f"trait_reasoning_{trait['trait']}_{selected_convo_data['conversation_id']}")
                        else:
                            st.info("No evaluation scores for this conversation.")

                    with detail_tabs[1]:
                        for message in selected_convo_data.get("conversation_log", []):
                            with st.chat_message(message.get('role', 'Unknown')):
                                st.markdown(message.get('content', ''))
                    
                    with detail_tabs[2]:
                        context_data = selected_convo_data.get("context", {})
                        if context_data:
                            display_context_file(context_data.get('supporting_documents', []))
                        else:
                            st.info("No context available for this conversation.")
                st.error(f"Failed to parse summary file: {summary_file}")
        else:
            st.error(f"evaluation_summary.json not found in {run_options[selected_run_name]}")

def finetuning_page(project_root):
    st.header("Finetuning Results")
    st.sidebar.title("Model Selection")
    finetuning_results_path = project_root / "evals" / "finetuning" / "finetuned_models.json"
    if finetuning_results_path.exists():
        with open(finetuning_results_path, 'r') as f:
            models = json.load(f)
        if not models:
            st.warning("No fine-tuned models found.")
            return

        df = pd.DataFrame(models)
        selected_model_id = st.sidebar.selectbox("Select a Model by Job ID", df['job_id'], key="finetune_model_selector")
        if selected_model_id:
            selected_model = df[df['job_id'] == selected_model_id].iloc[0]
            st.sidebar.subheader("Model Details")
            st.sidebar.json(selected_model.to_dict())

        st.dataframe(df)
        st.subheader("Stored Artifacts")
        st.info("Artifact linking is not yet implemented.")
    else:
        st.error(f"Finetuning results file not found at: {finetuning_results_path}")

if __name__ == "__main__":
    main()
