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
            if eval_name not in all_scores:
                all_scores[eval_name] = []
            
            score, _ = extract_score(eval_name, result)
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

def display_json_with_expanders(data, expand_level=1):
    """Recursively display JSON data with expanders for long fields."""
    if isinstance(data, dict):
        for key, value in data.items():
            # For 'context' files, we want to pretty-print the JSON content
            if key.endswith('.json') and isinstance(value, str):
                try:
                    # Attempt to parse the string as JSON
                    json_content = json.loads(value)
                    with st.expander(f"**{key}:** (JSON)", expanded=True):
                        st.json(json_content)
                except json.JSONDecodeError:
                    # If it's not valid JSON, treat as a regular (potentially long) string
                    if len(value) > 200:
                         with st.expander(f"**{key}:** (long text)"):
                            st.text(value)
                    else:
                        st.write(f"**{key}:** {value}")
            elif isinstance(value, (dict, list)) and len(value) > 0:
                # Use an expander for nested dictionaries or lists
                with st.expander(f"**{key}:** ({type(value).__name__})", expanded=expand_level > 0):
                    display_json_with_expanders(value, expand_level - 1)
            elif isinstance(value, str) and len(value) > 200:
                # Use an expander for any other long string
                with st.expander(f"**{key}:** (long text)"):
                    st.text(value)
            else:
                # Otherwise, just write the key-value pair
                st.write(f"**{key}:** {value}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)) and len(item) > 0:
                with st.expander(f"**Item {i}:** ({type(item).__name__})", expanded=expand_level > 0):
                    display_json_with_expanders(item, expand_level - 1)
            else:
                st.write(item)
    else:
        # For any other data type
        st.write(data)

def main(headless=False):
    """
    The main function for the Streamlit evaluation dashboard.
    If headless is True, it runs a quick check and exits.
    """
    st.set_page_config(layout="wide", page_title="Character Evaluation Dashboard")

    # Initialize session state
    if 'selected_run_dir' not in st.session_state:
        st.session_state.selected_run_dir = None
    if 'selected_convo_data' not in st.session_state:
        st.session_state.selected_convo_data = None

    project_root = find_project_root(__file__)
    if not project_root:
        st.error("Could not find the project root. Make sure you are running this from within the project.")
        return

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Evals", "Finetuning Results"])

    if page == "Evals":
        st.title("Character Evaluation Dashboard")
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
        selected_run_name = st.sidebar.selectbox("Select Evaluation Run", options=list(run_options.keys()))

        if selected_run_name:
            st.session_state.selected_run_dir = run_options[selected_run_name]

        if st.session_state.selected_run_dir:
            summary_file = st.session_state.selected_run_dir / "evaluation_summary.json"
            if summary_file.exists():
                try:
                    with open(summary_file, 'r') as f:
                        data = json.load(f)
                    
                    metadata = data.get("metadata", None)
                    if metadata:
                        st.sidebar.subheader("Evaluation Metadata")
                        st.sidebar.json(metadata)

                    results_per_conversation = data.get("results_per_conversation", [])

                    st.header("Aggregate Results")
                    aggregate_df = calculate_aggregate_metrics(results_per_conversation)
                    if not aggregate_df.empty:
                        st.dataframe(aggregate_df)
                    else:
                        st.warning("No evaluation results found to aggregate.")

                    st.header("Conversation Selector")
                    
                    sorted_conversations = sorted(
                        results_per_conversation,
                        key=lambda c: c.get('timestamp', c.get('start_time', 0)),
                        reverse=True
                    )
                    
                    convo_options = [None] + sorted_conversations
                    
                    def format_convo_option(convo):
                        if convo is None:
                            return "None"
                        return get_convo_display_name(convo)

                    selected_convo_data = st.selectbox(
                        'Select a Conversation to Drill Down',
                        options=convo_options,
                        format_func=format_convo_option,
                        index=0
                    )
                    st.session_state.selected_convo_data = selected_convo_data
                    
                    if selected_convo_data:
                        st.divider()
                        st.header("Conversation Details")
                        
                        detail_tabs = st.tabs(["Evaluation Scores", "Conversation Log", "Context"])

                        with detail_tabs[0]:
                            eval_results = selected_convo_data.get("evaluation_results", {})
                            if eval_results:
                                for eval_name, result in eval_results.items():
                                    st.subheader(eval_name.replace('_', ' ').title())
                                    if eval_name == "trait_adherence":
                                        score, reasoning = extract_score(eval_name, result)
                                        st.metric(label="Average Score", value=f"{score:.2f}/7" if not np.isnan(score) else "N/A")
                                        st.text_area("Overall Reasoning", reasoning, height=150, disabled=True, key=f"reasoning_{eval_name}")
                                        
                                        if "trait_scores" in result and result["trait_scores"]:
                                            with st.expander("Show Individual Trait Scores"):
                                                for trait_score in result["trait_scores"]:
                                                    trait_name = trait_score.get('trait', 'Unknown Trait')
                                                    trait_score_val = trait_score.get('score')
                                                    trait_reasoning = trait_score.get('reasoning', 'No reasoning provided.')
                                                    st.markdown(f"**Trait:** {trait_name}")
                                                    st.markdown(f"**Score:** {trait_score_val:.2f}/7" if trait_score_val is not None else "N/A")
                                                    st.text_area("Reasoning", trait_reasoning, height=100, disabled=True, key=f"trait_{trait_name}")
                                    else:
                                        score, reasoning = extract_score(eval_name, result)
                                        st.metric(label="Score", value=f"{score:.2f}/7" if not np.isnan(score) else "N/A")
                                        st.text_area("Reasoning", reasoning, height=100, disabled=True, key=f"reasoning_{eval_name}")
                            else:
                                st.info("No evaluation scores for this conversation.")

                        with detail_tabs[1]:
                            for message in selected_convo_data.get("conversation_log", []):
                                speaker = message.get("speaker", "Unknown")
                                text = message.get("message", "")
                                with st.chat_message("user" if speaker.lower() == "user" else "assistant"):
                                    st.write(text)
                        
                        with detail_tabs[2]:
                            context_data = selected_convo_data.get("context", {})
                            if context_data:
                                display_json_with_expanders(context_data)
                            else:
                                st.info("No context for this conversation.")
                                
                except json.JSONDecodeError:
                    st.error(f"Failed to parse the summary JSON file: {summary_file}")
            else:
                st.error(f"evaluation_summary.json not found in {st.session_state.selected_run_dir}")

    elif page == "Finetuning Results":
        st.title("Finetuning Results")
        st.sidebar.title("Model Selection")

        finetuning_results_path = project_root / "evals" / "finetuning" / "finetuned_models.json"
        if finetuning_results_path.exists():
            with open(finetuning_results_path, 'r') as f:
                models = json.load(f)
            
            if not models:
                st.warning("No fine-tuned models found.")
                return

            df = pd.DataFrame(models)
            
            selected_model_id = st.sidebar.selectbox("Select a Model by Job ID", df['job_id'])
            if selected_model_id:
                selected_model = df[df['job_id'] == selected_model_id].iloc[0]
                st.sidebar.subheader("Model Details")
                st.sidebar.write(selected_model)

            st.dataframe(df)
            st.subheader("Stored Artifacts")
            st.info("Artifact linking is not yet implemented.")
        else:
            st.error(f"Finetuning results file not found at: {finetuning_results_path}")

if __name__ == "__main__":
    main()
