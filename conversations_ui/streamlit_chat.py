import streamlit as st
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
import urllib.parse
import database as db
from database import (
    get_conversations, get_messages, save_conversation,
    get_conversation_by_message_id, rename_conversation, load_conversation_from_db
)
from llm_api import get_llm_response_stream, call_llm_api

# --- Constants and Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_PROMPTS_FILE = os.path.join(SCRIPT_DIR, "system_prompts.json")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
MAIN_DB = os.path.join(SCRIPT_DIR, "conversations.db")

ANTHROPIC_MODELS = [
    "anthropic/claude-3-5-haiku-latest",
    "anthropic/claude-sonnet-4-20250514",
    "anthropic/claude-opus-4-20250514",
]
OPENAI_MODELS = ["openai/gpt-4o-mini", "openai/o4-mini"]
OPENROUTER_MODELS = [
    "openrouter/qwen/qwen2.5-vl-32b-instruct",
    "openrouter/mistralai/mistral-small-3.2-24b-instruct",
    "openrouter/google/gemini-2.5-flash"
]
ALL_MODELS = OPENAI_MODELS + ANTHROPIC_MODELS + OPENROUTER_MODELS


# --- Helper Functions ---
def get_available_databases():
    """Scans for available .db files."""
    databases = {"Main Database": MAIN_DB}
    if os.path.exists(RESULTS_DIR):
        for f in sorted(os.listdir(RESULTS_DIR), reverse=True):
            if f.startswith("run_") and f.endswith(".db"):
                try:
                    ts_str = f.replace("run_", "").replace(".db", "")
                    dt_obj = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    name = f"Run: {dt_obj.strftime('%Y-%m-%d %H:%M')}"
                    databases[name] = os.path.join(RESULTS_DIR, f)
                except ValueError:
                    databases[f] = os.path.join(RESULTS_DIR, f)
    return databases


def generate_public_link(side_by_side: bool, unified_chat_input: bool):
    """Generate a public link with current configuration."""
    base_url = "https://character-training.streamlit.app/"  # Replace with your app's actual URL
    params = {
        'run_db': st.session_state.selected_db_path,
        'side_by_side': str(side_by_side).lower(),
        'unified_chat_input': str(unified_chat_input).lower()
    }
    
    # Add configuration for column 1
    if st.session_state.get('current_conversation_id_1'):
        params['convo_id_1'] = st.session_state['current_conversation_id_1']
    if st.session_state.get('model_1'):
        params['model_1'] = st.session_state['model_1']
    if st.session_state.get('persona_1'):
        params['persona_1'] = st.session_state['persona_1']
    
    # Add configuration for column 2 if side-by-side
    if side_by_side:
        if st.session_state.get('current_conversation_id_2'):
            params['convo_id_2'] = st.session_state['current_conversation_id_2']
        if st.session_state.get('model_2'):
            params['model_2'] = st.session_state['model_2']
        if st.session_state.get('persona_2'):
            params['persona_2'] = st.session_state['persona_2']
    
    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"


def rename_run_db(old_path: str, new_name: str) -> Optional[str]:
    """Renames a run database file."""
    if not old_path or not new_name or not os.path.exists(old_path):
        return None
    
    if not new_name.endswith(".db"):
        new_name += ".db"

    if not new_name.startswith("run_"):
        new_name = "run_" + new_name

    new_path = os.path.join(os.path.dirname(old_path), new_name)

    if os.path.exists(new_path):
        st.error(f"File '{new_name}' already exists.")
        return None
    
    try:
        os.rename(old_path, new_path)
        return new_path
    except OSError as e:
        st.error(f"Error renaming file: {e}")
        return None


def load_system_prompts() -> List[Dict]:
    """Loads system prompts from the JSON file."""
    try:
        with open(SYSTEM_PROMPTS_FILE, 'r') as f:
            return json.load(f).get("personas", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def format_persona_name(persona: Dict) -> str:
    """Formats a persona dictionary into a display name."""
    return f'{persona["name"]} ({persona["version"]})'


def get_persona_by_formatted_name(
    formatted_name: str, personas: List[Dict]
) -> Optional[Dict]:
    """Finds a persona dictionary by its formatted name."""
    for p in personas:
        if format_persona_name(p) == formatted_name:
            return p
    return None


def initialize_session_state():
    """Initializes Streamlit session state variables."""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.side_by_side = False
        st.session_state.selected_db_path = MAIN_DB
        st.session_state.current_conversation_id_1 = None
        st.session_state.current_conversation_id_2 = None
        st.session_state.messages_1 = []
        st.session_state.messages_2 = []
        st.session_state.jump_to_message_id_1 = None
        st.session_state.jump_to_message_id_2 = None


async def stream_and_display_response(
    target_column,
    system_prompt: str,
    messages_key: str,
    model: str,
    convo_id_key: str,
    persona_name: str
):
    """Streams the LLM response and updates the UI and database."""
    with target_column:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                async for chunk in get_llm_response_stream(
                    system_prompt, st.session_state[messages_key], model=model
                ):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"An error occurred: {e}")
                full_response = "Sorry, an error occurred."
                placeholder.markdown(full_response)

    st.session_state[messages_key].append(
        {"role": "assistant", "content": full_response}
    )
    # We don't get the message_id back from the stream, but it's saved in the DB
    save_conversation(
        st.session_state.selected_db_path,
        st.session_state.get(convo_id_key),
        "assistant",
        full_response,
        model=model,
        system_prompt_name=persona_name,
        system_prompt=system_prompt
    )
    # Manually trigger a rerun to update the message display with the new message ID
    # This is a workaround for the async nature of streaming
    if 'rerun_needed' not in st.session_state:
        st.session_state.rerun_needed = True


def render_chat_column(
    column, col_index: int, persona_options: List[Dict], system_prompts: List[Dict],
    side_by_side: bool, unified_chat_input: bool
):
    """Renders a single chat column, including selectors and messages."""
    convo_id_key = f"current_conversation_id_{col_index}"
    messages_key = f"messages_{col_index}"
    jump_key = f"jump_to_message_id_{col_index}"

    with column:
        st.header(f"Configuration {col_index}")

        # --- Conversation Selection and State ---
        conversations = get_conversations(st.session_state.selected_db_path)
        convo_map = {c['id']: c for c in conversations}
        convo_options = {
            c['id']: f"{c.get('name') or f'Convo {c['id'][:8]}...'} ({c['start_time']})"
            for c in conversations
        }
        convo_options[None] = "Start New Conversation"

        # Check if we need to jump to a message
        if st.session_state.get(jump_key):
            target_convo = get_conversation_by_message_id(
                st.session_state.selected_db_path, st.session_state[jump_key]
            )
            if target_convo:
                st.session_state[convo_id_key] = target_convo['id']
            st.session_state[jump_key] = None # Clear after jump
            st.rerun()

        def on_convo_change():
            convo_id = st.session_state[f"convo_select_{col_index}"]
            st.session_state[convo_id_key] = convo_id
            st.session_state[messages_key] = get_messages(st.session_state.selected_db_path, convo_id) if convo_id else []
            # Load model and persona from convo
            if convo_id and convo_id in convo_map:
                current_convo = convo_map[convo_id]
                if current_convo.get('model') in ALL_MODELS:
                    st.session_state[f"model_{col_index}"] = current_convo['model']
                if current_convo.get('system_prompt_name') in persona_options:
                    st.session_state[f"persona_{col_index}"] = current_convo['system_prompt_name']


        selected_convo_id = st.selectbox(
            f"Column {col_index} History",
            options=list(convo_options.keys()),
            format_func=lambda x: convo_options[x],
            key=f"convo_select_{col_index}",
            index=list(convo_options.keys()).index(st.session_state.get(convo_id_key))
            if st.session_state.get(convo_id_key) in convo_options else 0,
            on_change=on_convo_change
        )


        if selected_convo_id:
            # --- Rename Conversation ---
            rename_key = f"renaming_{col_index}"
            
            # Display current name with an edit button
            name_col, button_col = st.columns([4, 1])
            with name_col:
                current_name_display = convo_options.get(selected_convo_id, "Unnamed Conversation")
                st.markdown(f"**Name:** {current_name_display.split(' (')[0]}")
            with button_col:
                if st.button("✏️", key=f"edit_btn_{col_index}", help="Rename conversation"):
                    st.session_state[rename_key] = not st.session_state.get(rename_key, False)
                    st.rerun()

            if st.session_state.get(rename_key, False):
                current_name = convo_options.get(selected_convo_id, "Unnamed").split(" (")[0]
                new_name = st.text_input("New name", value=current_name, key=f"new_convo_name_{col_index}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save", key=f"save_rename_{col_index}"):
                        rename_conversation(st.session_state.selected_db_path, selected_convo_id, new_name)
                        st.session_state[rename_key] = False
                        st.rerun()
                with col2:
                    if st.button("Cancel", key=f"cancel_rename_{col_index}"):
                        st.session_state[rename_key] = False
                        st.rerun()

            # --- Share Conversation ---
            if st.button("Share", key=f"share_convo_{col_index}"):
                base_url = "http://localhost:8501" # Replace with your app's actual URL
                db_path_for_url = st.session_state.selected_db_path
                share_url = f"{base_url}?run_db={db_path_for_url}&convo_id={selected_convo_id}"
                st.code(share_url)
                st.info("Copy the link above to share this conversation.")


        # --- Model and Persona Selection ---
        current_convo = convo_map.get(st.session_state.get(convo_id_key))
        default_model_index = ALL_MODELS.index(st.session_state.get(f"model_{col_index}", current_convo.get('model') if current_convo else "openrouter/qwen/qwen2.5-vl-32b-instruct"))
        default_persona_index = persona_options.index(st.session_state.get(f"persona_{col_index}", current_convo.get('system_prompt_name') if current_convo else 'Agora, Collaborative Thinker (With Backstory)'))

        model = st.selectbox("Model", ALL_MODELS, key=f"model_{col_index}", index=default_model_index)
        
        # Persona selection with view prompt button
        persona_col, button_col = st.columns([4, 1])
        with persona_col:
            selected_persona_name = st.selectbox("Persona", persona_options, key=f"persona_{col_index}", index=default_persona_index)
        with button_col:
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing to align with selectbox
            if st.button("👁️ View", key=f"view_prompt_{col_index}", help="View system prompt and traits"):
                st.session_state[f"show_prompt_{col_index}"] = not st.session_state.get(f"show_prompt_{col_index}", False)
        
        persona = get_persona_by_formatted_name(selected_persona_name, system_prompts)
        system_prompt = persona['system_prompt'] if persona else ""
        persona_name = format_persona_name(persona) if persona else ""
        
        # Display system prompt and traits if toggled
        if st.session_state.get(f"show_prompt_{col_index}", False) and persona:
            with st.expander("📋 System Prompt & Character Traits", expanded=True):
                st.subheader("Character Traits")
                if persona.get('traits'):
                    for trait in persona['traits']:
                        st.markdown(f"• {trait}")
                else:
                    st.markdown("No traits defined for this persona")
                
                st.subheader("System Prompt")
                st.text_area("", value=system_prompt, height=300, disabled=True, key=f"prompt_display_{col_index}")

        # --- Jump to Message Input ---
        st.text_input("Jump to Message ID", key=f"jump_input_{col_index}", on_change=lambda: st.session_state.update({jump_key: st.session_state[f"jump_input_{col_index}"]}))

        # --- Display Messages ---
        for msg in st.session_state.get(messages_key, []):
            with st.chat_message(msg["role"]):
                # Create columns for message content and copy button
                msg_col, copy_col = st.columns([10, 1])
                
                with msg_col:
                    st.markdown(msg["content"])
                    if msg.get('id'):
                        st.caption(f"ID: {msg['id']}")
                
                with copy_col:
                    # Add copy button with unique key
                    copy_key = f"copy_{col_index}_{msg.get('id', hash(msg['content']))}"
                    if st.button("📋", key=copy_key, help="Copy message"):
                        # Use JavaScript to copy to clipboard
                        copy_js = f"""
                        <script>
                        navigator.clipboard.writeText(`{msg['content'].replace('`', '\`')}`);
                        </script>
                        """
                        st.components.v1.html(copy_js, height=0)
                        st.success("Copied to clipboard!", icon="✅")

        # --- Individual Chat Input ---
        prompt = None
        if side_by_side and not unified_chat_input:
            prompt = st.chat_input("Send message", key=f"chat_input_{col_index}")

    return model, persona_name, system_prompt, prompt


def main():
    """Main function to run the Streamlit chatbot application."""
    st.set_page_config(layout="wide", page_title="LLM Persona Evaluator")
    st.title("LLM Persona Evaluator")
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Chat Interface", "Analysis", "Evaluations"])
    
    with tab1:
        main_chat_interface()
    
    with tab2:
        display_analysis_interface()
    
    with tab3:
        display_evaluation_dashboard()


def main_chat_interface():
    """Main chat interface functionality."""

    system_prompts = load_system_prompts()
    persona_options = [format_persona_name(p) for p in system_prompts]

    initialize_session_state()

    # --- Query Params Handling ---
    if "query_params_processed" not in st.session_state:
        query_params = st.query_params.to_dict()
        
        # Handle database selection
        if "run_db" in query_params:
            requested_db = query_params["run_db"]
            # Validate that the database file exists, otherwise use default
            if os.path.exists(requested_db):
                st.session_state.selected_db_path = requested_db
            else:
                st.session_state.selected_db_path = MAIN_DB
                st.warning(f"Database file not found: {requested_db}. Using default database.")
        
        # Handle side-by-side configuration
        if "side_by_side" in query_params:
            st.session_state.side_by_side = query_params["side_by_side"].lower() == "true"
        
        # Handle unified chat input
        if "unified_chat_input" in query_params:
            st.session_state.unified_chat_input = query_params["unified_chat_input"].lower() == "true"
        
        # Handle column 1 configuration
        if "convo_id_1" in query_params:
            convo_id = query_params["convo_id_1"]
            try:
                # Check if the conversation exists in the current database
                messages = get_messages(st.session_state.selected_db_path, convo_id) if convo_id else []
                if messages or convo_id is None:
                    st.session_state.current_conversation_id_1 = convo_id
                    st.session_state.messages_1 = messages
                    
                    if os.path.exists(st.session_state.selected_db_path):
                        convo = load_conversation_from_db(st.session_state.selected_db_path, convo_id)
                        if convo:
                            st.session_state["model_1"] = convo.get("model")
                            st.session_state["persona_1"] = convo.get("system_prompt_name")
                else:
                    # Conversation doesn't exist in this database
                    st.warning(f"Conversation {convo_id[:8]}... not found in current database. Starting with empty conversation.")
                    st.session_state.current_conversation_id_1 = None
                    st.session_state.messages_1 = []
            except Exception as e:
                st.error(f"Error loading conversation: {e}")
                st.session_state.current_conversation_id_1 = None
                st.session_state.messages_1 = []
        
        if "model_1" in query_params:
            st.session_state["model_1"] = query_params["model_1"]
        if "persona_1" in query_params:
            st.session_state["persona_1"] = query_params["persona_1"]
        
        # Handle column 2 configuration  
        if "convo_id_2" in query_params:
            convo_id = query_params["convo_id_2"]
            try:
                # Check if the conversation exists in the current database
                messages = get_messages(st.session_state.selected_db_path, convo_id) if convo_id else []
                if messages or convo_id is None:
                    st.session_state.current_conversation_id_2 = convo_id
                    st.session_state.messages_2 = messages
                    
                    if os.path.exists(st.session_state.selected_db_path):
                        convo = load_conversation_from_db(st.session_state.selected_db_path, convo_id)
                        if convo:
                            st.session_state["model_2"] = convo.get("model")
                            st.session_state["persona_2"] = convo.get("system_prompt_name")
                else:
                    # Conversation doesn't exist in this database
                    st.warning(f"Conversation {convo_id[:8]}... not found in current database. Starting with empty conversation.")
                    st.session_state.current_conversation_id_2 = None
                    st.session_state.messages_2 = []
            except Exception as e:
                st.error(f"Error loading conversation: {e}")
                st.session_state.current_conversation_id_2 = None
                st.session_state.messages_2 = []
        
        if "model_2" in query_params:
            st.session_state["model_2"] = query_params["model_2"]
        if "persona_2" in query_params:
            st.session_state["persona_2"] = query_params["persona_2"]
        
        # Legacy support for old convo_id parameter
        if "convo_id" in query_params and "convo_id_1" not in query_params:
            convo_id = query_params["convo_id"]
            st.session_state.current_conversation_id_1 = convo_id
            try:
                st.session_state.messages_1 = get_messages(st.session_state.selected_db_path, convo_id) if convo_id else []
            except Exception as e:
                st.error(f"Error loading conversation: {e}")
                st.session_state.messages_1 = []

        st.session_state["query_params_processed"] = True
        st.rerun()


    # --- Sidebar Setup ---
    st.sidebar.title("Controls")
    available_dbs = get_available_databases()
    # Find index of current db_path
    db_values = list(available_dbs.values())
    db_keys = list(available_dbs.keys())
    current_db_index = db_values.index(st.session_state.selected_db_path) if st.session_state.selected_db_path in db_values else 0

    selected_db_name = st.sidebar.selectbox(
        "Select Database", options=db_keys, index=current_db_index
    )
    st.session_state.selected_db_path = available_dbs[selected_db_name]
    st.sidebar.info(f"DB: `{os.path.basename(st.session_state.selected_db_path)}`")

    if st.session_state.selected_db_path != MAIN_DB:
        new_run_name = st.sidebar.text_input("Rename Run", key="new_run_name")
        if st.sidebar.button("Rename"):
            if new_run_name:
                new_path = rename_run_db(st.session_state.selected_db_path, new_run_name)
                if new_path:
                    st.session_state.selected_db_path = new_path
                    st.rerun()

    side_by_side = st.sidebar.toggle("Side-by-side comparison", value=st.session_state.get('side_by_side', False))
    st.session_state.side_by_side = side_by_side

    unified_chat_input = True
    if side_by_side:
        unified_chat_input = st.sidebar.toggle("Unified Chat Input", value=st.session_state.get('unified_chat_input', True))

    # --- Get Public Link Button ---
    if st.sidebar.button("🔗 Get Public Link"):
        public_link = generate_public_link(side_by_side, unified_chat_input)
        st.sidebar.code(public_link, language=None)
        st.sidebar.info("Copy the link above to share this configuration.")

    columns = st.columns(2) if side_by_side else [st.container()]

    # --- Render Chat Columns ---
    model_1, persona_name_1, system_prompt_1, prompt_1 = render_chat_column(
        columns[0], 1, persona_options, system_prompts, side_by_side, unified_chat_input
    )

    model_2, persona_name_2, system_prompt_2, prompt_2 = (None, None, None, None)
    if side_by_side and len(columns) > 1:
        model_2, persona_name_2, system_prompt_2, prompt_2 = render_chat_column(
            columns[1], 2, persona_options, system_prompts, side_by_side, unified_chat_input
        )

    # --- Unified Chat Input Logic ---
    unified_prompt = None
    if not side_by_side:
        unified_prompt = st.chat_input("Your message...", key="single_chat_input")
    elif unified_chat_input:
        unified_prompt = st.chat_input("Send a message to both...", key="unified_chat_input")

    async def handle_response(prompt, col_index, model, persona_name, system_prompt):
        messages_key = f"messages_{col_index}"
        convo_id_key = f"current_conversation_id_{col_index}"

        st.session_state[messages_key].append({"role": "user", "content": prompt})
        convo_id, msg_id = save_conversation(
            st.session_state.selected_db_path, st.session_state.get(convo_id_key),
            "user", prompt, model=model, system_prompt_name=persona_name,
            system_prompt=system_prompt
        )
        st.session_state[convo_id_key] = convo_id
        st.session_state[messages_key][-1]['id'] = msg_id


    async def run_all_responses(prompt):
        tasks = []
        # Fire off the first response
        tasks.append(stream_and_display_response(
            columns[0], system_prompt_1, "messages_1", model_1,
            "current_conversation_id_1", persona_name_1
        ))
        # Fire off the second response if in side-by-side mode
        if side_by_side and len(columns) > 1:
            tasks.append(stream_and_display_response(
                columns[1], system_prompt_2, "messages_2", model_2,
                "current_conversation_id_2", persona_name_2
            ))
        await asyncio.gather(*tasks)


    if unified_prompt:
        # Handle message for column 1
        asyncio.run(handle_response(unified_prompt, 1, model_1, persona_name_1, system_prompt_1))
        # Handle message for column 2 if in side-by-side mode
        if side_by_side and model_2:
            asyncio.run(handle_response(unified_prompt, 2, model_2, persona_name_2, system_prompt_2))
        # Now run the assistant responses for both columns
        asyncio.run(run_all_responses(unified_prompt))

    if prompt_1:
        asyncio.run(handle_response(prompt_1, 1, model_1, persona_name_1, system_prompt_1))
        asyncio.run(stream_and_display_response(
            columns[0], system_prompt_1, "messages_1", model_1,
            "current_conversation_id_1", persona_name_1
        ))

    if prompt_2:
        asyncio.run(handle_response(prompt_2, 2, model_2, persona_name_2, system_prompt_2))
        asyncio.run(stream_and_display_response(
            columns[1], system_prompt_2, "messages_2", model_2,
            "current_conversation_id_2", persona_name_2
        ))

    if st.session_state.get('rerun_needed'):
        del st.session_state['rerun_needed']
        st.rerun()


def display_analysis_interface():
    """Display the existing analysis functionality."""
    st.header("Analysis Interface")
    st.info("This tab would contain the existing analysis functionality. "
           "You can move the analyze_results.py functionality here if needed.")


def display_evaluation_dashboard():
    """Display evaluation results dashboard."""
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        import sqlite3
        import pandas as pd
        from glob import glob
    except ImportError as e:
        st.error(f"Missing required packages: {e}. Please install with: pip install plotly pandas")
        return
    
    st.header("Evaluation Results Dashboard")
    
    eval_type = st.selectbox("Evaluation Type", ["summary", "single", "elo"])
    
    if eval_type == "summary":
        display_evaluation_summaries()
    elif eval_type == "single":
        display_single_evaluations()
    elif eval_type == "elo":
        display_elo_evaluations()


def display_evaluation_summaries():
    """Display evaluation summaries overview."""
    st.subheader("Evaluation Summaries")
    
    # Look for evaluation results directories
    eval_dirs = glob("evaluation_results/*/")
    eval_dirs.extend(glob("evaluation_data/*/"))
    eval_dirs.extend(glob("evaluation_data/*/evaluation_results/"))
    
    if not eval_dirs:
        st.warning("No evaluation results found. Run evaluations first using judge_conversations.py")
        return
    
    summary_files = []
    for eval_dir in eval_dirs:
        summary_file = os.path.join(eval_dir, "evaluation_summaries.db")
        if os.path.exists(summary_file):
            summary_files.append(summary_file)
    
    if not summary_files:
        st.warning("No evaluation summary files found.")
        return
    
    # File selector
    selected_file = st.selectbox("Select Evaluation Run", summary_files)
    
    if selected_file:
        summaries = load_summaries_from_db(selected_file)
        
        if summaries:
            # Overview metrics
            st.subheader("Overview")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Files Evaluated", len(summaries))
            with col2:
                avg_score = sum(s['overall_score'] for s in summaries) / len(summaries)
                st.metric("Avg Overall Score", f"{avg_score:.2f}")
            with col3:
                st.metric("Evaluation Date", summaries[0]['created_at'][:10])
            
            # Individual results
            st.subheader("Results by Model/Configuration")
            for summary in summaries:
                with st.expander(f"Results for {os.path.basename(summary['filepath'])}"):
                    display_filepath_summary(summary)


def display_single_evaluations():
    """Display single evaluation results."""
    try:
        import pandas as pd
        from glob import glob
    except ImportError as e:
        st.error(f"Missing required packages: {e}")
        return
        
    st.subheader("Single Evaluation Results")
    
    # Look for single judgment files
    judgment_files = glob("evaluation_results/*/single_judgments.db")
    judgment_files.extend(glob("evaluation_data/*/evaluation_results/single_judgments.db"))
    
    if not judgment_files:
        st.warning("No single evaluation results found.")
        return
    
    selected_file = st.selectbox("Select Judgment File", judgment_files)
    
    if selected_file:
        judgments = load_single_judgments_from_db(selected_file)
        
        if judgments:
            # Summary statistics
            st.subheader("Summary Statistics")
            trait_stats = calculate_trait_statistics(judgments)
            st.dataframe(trait_stats)
            
            # Individual conversation details
            st.subheader("Individual Conversation Evaluations")
            for judgment in judgments:
                with st.expander(f"Conversation {judgment['conversation_id'][:8]}..."):
                    st.write("**Overall Reasoning:**", judgment['overall_reasoning'])
                    
                    # Display trait judgments
                    trait_data = []
                    for tj in judgment['trait_judgments']:
                        trait_data.append({
                            'Trait': tj['trait'],
                            'Score': tj['score'],
                            'Reasoning': tj['reasoning']
                        })
                    
                    if trait_data:
                        df = pd.DataFrame(trait_data)
                        st.dataframe(df)


def display_elo_evaluations():
    """Display ELO evaluation results."""
    try:
        import pandas as pd
        from glob import glob
    except ImportError as e:
        st.error(f"Missing required packages: {e}")
        return
        
    st.subheader("ELO Evaluation Results")
    
    # Look for ELO comparison files
    comparison_files = glob("evaluation_results/*/elo_comparisons.db")
    comparison_files.extend(glob("evaluation_data/*/evaluation_results/elo_comparisons.db"))
    
    if not comparison_files:
        st.warning("No ELO evaluation results found.")
        return
    
    selected_file = st.selectbox("Select Comparison File", comparison_files)
    
    if selected_file:
        comparisons = load_elo_comparisons_from_db(selected_file)
        
        if comparisons:
            # Group by trait
            traits = list(set(comp['trait'] for comp in comparisons))
            
            st.subheader("ELO Rankings by Trait")
            for trait in traits:
                trait_comparisons = [comp for comp in comparisons if comp['trait'] == trait]
                
                with st.expander(f"{trait} Rankings"):
                    for comparison in trait_comparisons:
                        st.write("**Reasoning:**", comparison['reasoning'])
                        
                        # Create rankings dataframe
                        rankings_data = []
                        for ranking in comparison['rankings']:
                            rankings_data.append({
                                'Conversation ID': ranking['conversation_id'][:8] + '...',
                                'Rank': ranking['rank'],
                                'Score': ranking['score']
                            })
                        
                        if rankings_data:
                            df = pd.DataFrame(rankings_data)
                            df = df.sort_values('Rank')
                            st.dataframe(df)


def display_filepath_summary(summary):
    """Display detailed results for a single filepath."""
    import plotly.graph_objects as go
    
    # Overall score
    st.metric("Overall Score", f"{summary['overall_score']:.2f}")
    
    # Parse trait summaries if available
    if summary.get('trait_summaries_json'):
        import json
        try:
            trait_summaries = json.loads(summary['trait_summaries_json'])
            
            if trait_summaries:
                st.subheader("Trait Scores")
                
                # Create radar chart
                traits = [ts['trait'] for ts in trait_summaries]
                scores = [ts['average_score'] for ts in trait_summaries]
                
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=scores,
                    theta=traits,
                    fill='toself',
                    name='Trait Scores'
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 5]
                        )),
                    showlegend=False,
                    title="Trait Score Profile"
                )
                st.plotly_chart(fig)
                
                # Detailed trait breakdown
                for trait_summary in trait_summaries:
                    with st.expander(f"{trait_summary['trait']} Details"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Average Score", f"{trait_summary['average_score']:.2f}")
                            st.metric("Std Deviation", f"{trait_summary['std_deviation']:.2f}")
                        with col2:
                            # Score distribution
                            dist = trait_summary.get('score_distribution', {})
                            if dist:
                                scores = list(dist.keys())
                                counts = list(dist.values())
                                
                                fig = go.Figure([go.Bar(x=scores, y=counts)])
                                fig.update_layout(
                                    title="Score Distribution",
                                    xaxis_title="Score",
                                    yaxis_title="Count"
                                )
                                st.plotly_chart(fig, use_container_width=True)
        except json.JSONDecodeError:
            st.error("Could not parse trait summaries data")


def load_summaries_from_db(db_path):
    """Load evaluation summaries from database."""
    import sqlite3
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM evaluation_summaries ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        st.error(f"Error loading summaries from {db_path}: {e}")
        return []


def load_single_judgments_from_db(db_path):
    """Load single judgments from database."""
    import sqlite3
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM single_judgments ORDER BY created_at DESC")
            judgments = []
            for row in cursor.fetchall():
                judgment = dict(row)
                # Parse trait judgments JSON
                if judgment.get('trait_judgments_json'):
                    import json
                    try:
                        judgment['trait_judgments'] = json.loads(judgment['trait_judgments_json'])
                    except json.JSONDecodeError:
                        judgment['trait_judgments'] = []
                judgments.append(judgment)
            return judgments
    except sqlite3.Error as e:
        st.error(f"Error loading judgments from {db_path}: {e}")
        return []


def load_elo_comparisons_from_db(db_path):
    """Load ELO comparisons from database."""
    import sqlite3
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM elo_comparisons ORDER BY created_at DESC")
            comparisons = []
            for row in cursor.fetchall():
                comparison = dict(row)
                # Parse rankings JSON
                if comparison.get('rankings_json'):
                    import json
                    try:
                        comparison['rankings'] = json.loads(comparison['rankings_json'])
                    except json.JSONDecodeError:
                        comparison['rankings'] = []
                comparisons.append(comparison)
            return comparisons
    except sqlite3.Error as e:
        st.error(f"Error loading comparisons from {db_path}: {e}")
        return []


def calculate_trait_statistics(judgments):
    """Calculate summary statistics for traits across all judgments."""
    import pandas as pd
    
    trait_data = {}
    
    for judgment in judgments:
        for tj in judgment.get('trait_judgments', []):
            trait = tj['trait']
            score = tj['score']
            
            if trait not in trait_data:
                trait_data[trait] = []
            trait_data[trait].append(score)
    
    # Calculate statistics
    stats = []
    for trait, scores in trait_data.items():
        stats.append({
            'Trait': trait,
            'Average Score': sum(scores) / len(scores),
            'Min Score': min(scores),
            'Max Score': max(scores),
            'Count': len(scores)
        })
    
    return pd.DataFrame(stats)


if __name__ == "__main__":
    main()