import streamlit as st
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
import urllib.parse
from glob import glob
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
        st.session_state.unified_chat_input = True


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
        
        # Get available models including fine-tuned ones
        available_models = get_available_models_with_finetuned()
        
        # Find current model or default
        current_model = st.session_state.get(f"model_{col_index}", current_convo.get('model') if current_convo else "openrouter/qwen/qwen2.5-vl-32b-instruct")
        
        # Make sure the current model is in the available models list
        if current_model not in available_models:
            available_models.append(current_model)
        
        default_model_index = available_models.index(current_model) if current_model in available_models else 0
        default_persona_index = persona_options.index(st.session_state.get(f"persona_{col_index}", current_convo.get('system_prompt_name') if current_convo else 'Agora, Collaborative Thinker (With Backstory)'))

        model = st.selectbox("Model", available_models, key=f"model_{col_index}", index=default_model_index)
        
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
                        navigator.clipboard.writeText(`{msg['content'].replace('`', '\\`')}`);
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Chat Interface", "Analysis", "Evaluations", "Prompt Testing", "Research Logs", "Analytics Dashboard"])
    
    with tab1:
        main_chat_interface()
    
    with tab2:
        display_analysis_interface()
    
    with tab3:
        display_evaluation_dashboard()
    
    with tab4:
        display_prompt_testing_interface()
    
    with tab5:
        display_research_logs_interface()
    
    with tab6:
        display_analytics_dashboard()


def main_chat_interface():
    """Main chat interface functionality."""

    system_prompts = load_system_prompts()
    persona_options = [format_persona_name(p) for p in system_prompts]

    initialize_session_state()

    # --- Query Params Handling (must happen before any widgets are rendered) ---
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
        else:
            # Set default if not specified
            st.session_state.unified_chat_input = True
        
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

    # --- Start New Conversation Button ---
    if st.sidebar.button("🆕 Start New Conversation", use_container_width=True):
        # Reset only conversation state, keep all other configurations
        st.session_state.current_conversation_id_1 = None
        st.session_state.current_conversation_id_2 = None
        st.session_state.messages_1 = []
        st.session_state.messages_2 = []
        st.session_state.jump_to_message_id_1 = None
        st.session_state.jump_to_message_id_2 = None
        # Keep all other settings like model, persona, side_by_side, etc.
        st.rerun()

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
        st.session_state.unified_chat_input = unified_chat_input

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
        unified_prompt = st.chat_input("Send a message to both...", key="unified_chat_input_widget")

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


def display_prompt_testing_interface():
    """Display the prompt testing interface."""
    try:
        from prompt_tester import display_prompt_tester
        display_prompt_tester()
    except ImportError as e:
        st.error(f"Could not load prompt tester: {e}")
        st.info("Please ensure all dependencies are installed.")


def display_research_logs_interface():
    """Display the comprehensive research logs interface for debugging and prompt improvement."""
    try:
        from research_logger import display_research_logs, display_log_analysis
        
        st.header("🔍 Research Logs & Debugging")
        st.write("Comprehensive logging system for tracking prompt performance, API calls, evaluations, and debugging information.")
        
        # Create sub-tabs for different log views
        subtab1, subtab2, subtab3, subtab4 = st.tabs(["📋 All Logs", "🤖 LLM Logs", "📊 Log Analysis", "🎯 Quick Actions"])
        
        with subtab1:
            display_research_logs()
        
        with subtab2:
            display_llm_logs()
        
        with subtab3:
            display_log_analysis()
        
        with subtab4:
            display_research_quick_actions()
            
    except ImportError as e:
        st.error(f"Could not load research logger: {e}")
        st.info("The research logging system is not available. Please ensure all dependencies are installed.")


def display_analytics_dashboard():
    """Display the new analytics dashboard."""
    try:
        from analytics_dashboard import AnalyticsDashboard
        
        # Get the current database path from session state
        db_path = st.session_state.get('selected_db_path', MAIN_DB)
        
        dashboard = AnalyticsDashboard(db_path)
        dashboard.render_dashboard()
        
    except ImportError as e:
        st.error(f"Could not load analytics dashboard: {e}")
        st.info("The analytics dashboard is not available. Please ensure all dependencies are installed.")
        
        # Show fallback information
        st.header("📊 Analytics Dashboard")
        st.write("Advanced analytics and monitoring for the character training system.")
        
        st.subheader("Features:")
        st.write("- **System Overview**: Real-time health monitoring and performance metrics")
        st.write("- **Evaluation Metrics**: Comprehensive evaluation performance tracking")
        st.write("- **Bias Detection**: Automated bias pattern detection and alerting")
        st.write("- **Performance Monitoring**: Response time, throughput, and error rate tracking")
        st.write("- **Prompt Testing**: A/B testing and statistical analysis of prompt effectiveness")
        st.write("- **Logs & Alerts**: Centralized logging and alert management")
        
        st.info("Install required dependencies: `pip install plotly scipy numpy pandas`")


def display_llm_logs():
    """Display dedicated LLM logs interface for easy prompt debugging."""
    try:
        from research_logger import get_research_logger
        
        st.subheader("🤖 LLM Logs - Prompt Debugging")
        st.write("Detailed view of all LLM interactions with system prompts, user prompts, and model responses.")
        
        logger = get_research_logger()
        
        # Get LLM-specific logs
        all_logs = logger.get_logs()
        llm_logs = [log for log in all_logs if log.get('type') in ['api_call', 'llm_generation']]
        
        if not llm_logs:
            st.info("No LLM logs available. Start using the system to generate LLM logs.")
            
            # Add some sample LLM logs for demonstration
            if st.button("🔧 Generate Sample LLM Logs"):
                # Create sample logs to demonstrate the interface
                logger.log_llm_generation(
                    generation_type="scenario_generation",
                    system_prompt="You are a helpful assistant that generates evaluation scenarios for AI character testing.",
                    user_prompt="Generate 3 scenarios that test collaborative behavior in AI characters.",
                    model_response="Here are 3 scenarios for testing collaborative behavior:\n\n1. Team Project Scenario: A user is working on a group project...",
                    model="claude-3-5-sonnet-20241022",
                    tokens_used=450,
                    response_time=2.3,
                    context={"scenario_count": 3, "trait_focus": "collaborative"}
                )
                
                logger.log_api_call(
                    endpoint="anthropic/claude-3-5-sonnet-20241022",
                    prompt="Please evaluate this conversation for collaborative traits on a 1-5 scale.",
                    response="{\n  \"collaborative_score\": 4.2,\n  \"reasoning\": \"The assistant demonstrates good collaborative behavior...\"\n}",
                    model="claude-3-5-sonnet-20241022",
                    system_prompt="You are a judge evaluating AI conversations for collaborative traits.",
                    prompt_type="judge_evaluation",
                    tokens_used=320,
                    response_time=1.8
                )
                
                st.success("Sample LLM logs generated! Refresh to see them.")
                st.rerun()
            
            return
        
        # LLM logs overview
        st.subheader("📊 LLM Logs Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total LLM Calls", len(llm_logs))
        
        with col2:
            api_calls = len([log for log in llm_logs if log.get('type') == 'api_call'])
            st.metric("API Calls", api_calls)
        
        with col3:
            generations = len([log for log in llm_logs if log.get('type') == 'llm_generation'])
            st.metric("Generations", generations)
        
        with col4:
            errors = len([log for log in llm_logs if not log.get('success', True)])
            st.metric("Errors", errors)
        
        # Filter options
        st.subheader("🔍 Filter LLM Logs")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            log_type_filter = st.selectbox("Log Type", ["All", "API Calls", "Generations"], key="llm_log_type")
        
        with col2:
            model_filter = st.selectbox("Model", ["All"] + list(set([log.get('model', 'Unknown') for log in llm_logs])), key="llm_model")
        
        with col3:
            prompt_type_filter = st.selectbox("Prompt Type", ["All"] + list(set([log.get('prompt_type', log.get('generation_type', 'Unknown')) for log in llm_logs])), key="llm_prompt_type")
        
        # Apply filters
        filtered_logs = llm_logs
        
        if log_type_filter == "API Calls":
            filtered_logs = [log for log in filtered_logs if log.get('type') == 'api_call']
        elif log_type_filter == "Generations":
            filtered_logs = [log for log in filtered_logs if log.get('type') == 'llm_generation']
        
        if model_filter != "All":
            filtered_logs = [log for log in filtered_logs if log.get('model') == model_filter]
        
        if prompt_type_filter != "All":
            filtered_logs = [log for log in filtered_logs if log.get('prompt_type') == prompt_type_filter or log.get('generation_type') == prompt_type_filter]
        
        # Display filtered logs
        st.subheader(f"🤖 LLM Logs ({len(filtered_logs)} entries)")
        
        if not filtered_logs:
            st.info("No logs match the current filters.")
            return
        
        # Display each log with full prompt details
        for i, log in enumerate(reversed(filtered_logs)):
            timestamp = log.get('timestamp', 'Unknown')
            log_type = log.get('type', 'unknown')
            model = log.get('model', 'Unknown')
            success = log.get('success', True)
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = timestamp
            
            # Choose icon based on type
            if log_type == 'api_call':
                icon = "🔗"
                type_display = "API Call"
            elif log_type == 'llm_generation':
                icon = "🤖"
                type_display = "LLM Generation"
            else:
                icon = "📝"
                type_display = log_type.replace('_', ' ').title()
            
            # Status indicator
            status_icon = "✅" if success else "❌"
            
            # Create expandable entry
            with st.expander(f"{icon} {time_str} - {type_display} ({model}) {status_icon}", expanded=False):
                
                # Show basic info
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type:** {type_display}")
                    st.write(f"**Model:** {model}")
                    st.write(f"**Time:** {time_str}")
                
                with col2:
                    if log.get('tokens_used'):
                        st.write(f"**Tokens Used:** {log['tokens_used']}")
                    if log.get('response_time'):
                        st.write(f"**Response Time:** {log['response_time']:.2f}s")
                    if log.get('prompt_type') or log.get('generation_type'):
                        st.write(f"**Prompt Type:** {log.get('prompt_type', log.get('generation_type', 'Unknown'))}")
                
                # Show error if any
                if not success and log.get('error'):
                    st.error(f"**Error:** {log['error']}")
                
                # Show prompts and responses
                if log_type == 'api_call':
                    # System prompt
                    if log.get('system_prompt'):
                        st.subheader("🎯 System Prompt")
                        st.code(log['system_prompt'], language="text")
                    
                    # User prompt
                    st.subheader("📝 User Prompt")
                    st.code(log['prompt'], language="text")
                    
                    # Model response
                    st.subheader("📤 Model Response")
                    st.code(log['response'], language="text")
                    
                    # Context
                    if log.get('conversation_context'):
                        st.subheader("💬 Context")
                        st.json(log['conversation_context'])
                
                elif log_type == 'llm_generation':
                    # System prompt
                    st.subheader("🎯 System Prompt")
                    st.code(log['system_prompt'], language="text")
                    
                    # User prompt
                    st.subheader("📝 User Prompt")
                    st.code(log['user_prompt'], language="text")
                    
                    # Model response
                    st.subheader("📤 Model Response")
                    st.code(log['model_response'], language="text")
                    
                    # Generation context
                    if log.get('context'):
                        st.subheader("🔍 Generation Context")
                        st.json(log['context'])
                
                # Copy buttons for easy prompt reuse
                st.subheader("🔧 Quick Actions")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📋 Copy System Prompt", key=f"copy_system_{i}"):
                        system_prompt = log.get('system_prompt', '')
                        st.code(system_prompt, language="text")
                        st.success("System prompt displayed above for copying!")
                
                with col2:
                    if st.button("📋 Copy User Prompt", key=f"copy_user_{i}"):
                        user_prompt = log.get('prompt', log.get('user_prompt', ''))
                        st.code(user_prompt, language="text")
                        st.success("User prompt displayed above for copying!")
                
                with col3:
                    if st.button("📋 Copy Response", key=f"copy_response_{i}"):
                        response = log.get('response', log.get('model_response', ''))
                        st.code(response, language="text")
                        st.success("Response displayed above for copying!")
        
        # Export LLM logs
        st.subheader("📁 Export LLM Logs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export Filtered LLM Logs"):
                import json
                json_str = json.dumps(filtered_logs, indent=2)
                st.download_button(
                    label="Download LLM Logs",
                    data=json_str,
                    file_name=f"llm_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📊 Generate LLM Report"):
                report = generate_llm_report(filtered_logs)
                st.download_button(
                    label="Download LLM Report",
                    data=report,
                    file_name=f"llm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
                
    except ImportError as e:
        st.error(f"Could not load research logger: {e}")


def generate_llm_report(llm_logs):
    """Generate a comprehensive LLM usage report."""
    from datetime import datetime
    
    total_logs = len(llm_logs)
    api_calls = len([log for log in llm_logs if log.get('type') == 'api_call'])
    generations = len([log for log in llm_logs if log.get('type') == 'llm_generation'])
    errors = len([log for log in llm_logs if not log.get('success', True)])
    
    # Calculate token usage
    total_tokens = sum([log.get('tokens_used', 0) for log in llm_logs if log.get('tokens_used')])
    
    # Calculate response times
    response_times = [log.get('response_time', 0) for log in llm_logs if log.get('response_time')]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Model usage
    models = {}
    for log in llm_logs:
        model = log.get('model', 'Unknown')
        if model not in models:
            models[model] = 0
        models[model] += 1
    
    # Prompt types
    prompt_types = {}
    for log in llm_logs:
        prompt_type = log.get('prompt_type', log.get('generation_type', 'Unknown'))
        if prompt_type not in prompt_types:
            prompt_types[prompt_type] = 0
        prompt_types[prompt_type] += 1
    
    report = f"""# LLM Usage Report

## Overview
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total LLM Interactions:** {total_logs}
- **API Calls:** {api_calls}
- **Generations:** {generations}
- **Errors:** {errors}
- **Success Rate:** {((total_logs - errors) / total_logs * 100):.1f}%

## Performance Metrics
- **Total Tokens Used:** {total_tokens:,}
- **Average Response Time:** {avg_response_time:.2f}s
- **Fastest Response:** {min(response_times):.2f}s
- **Slowest Response:** {max(response_times):.2f}s

## Model Usage
"""
    
    for model, count in models.items():
        percentage = (count / total_logs) * 100
        report += f"- **{model}:** {count} calls ({percentage:.1f}%)\n"
    
    report += f"""
## Prompt Types
"""
    
    for prompt_type, count in prompt_types.items():
        percentage = (count / total_logs) * 100
        report += f"- **{prompt_type}:** {count} calls ({percentage:.1f}%)\n"
    
    if errors > 0:
        report += f"""
## Error Analysis
- **Total Errors:** {errors}
- **Error Rate:** {(errors / total_logs * 100):.1f}%

### Recent Errors:
"""
        error_logs = [log for log in llm_logs if not log.get('success', True)]
        for log in error_logs[-5:]:
            report += f"- {log.get('timestamp', 'Unknown')}: {log.get('error', 'Unknown error')}\n"
    
    return report


def display_research_quick_actions():
    """Display quick actions for researchers."""
    st.subheader("🎯 Quick Actions for Researchers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Log a Manual Test")
        with st.form("manual_test_form"):
            prompt_type = st.selectbox("Prompt Type", ["character_card", "scenario_generation", "judge_prompt", "system_prompt"])
            test_input = st.text_area("Test Input", height=100)
            test_output = st.text_area("Test Output", height=100)
            notes = st.text_area("Notes/Observations", height=60)
            
            if st.form_submit_button("Log Test"):
                if test_input and test_output:
                    try:
                        from research_logger import get_research_logger
                        logger = get_research_logger()
                        
                        logger.log_prompt_test(
                            prompt_type=prompt_type,
                            prompt_version="manual_test",
                            input_data={"prompt": test_input, "notes": notes},
                            output_data={"response": test_output, "manual_test": True}
                        )
                        st.success("Test logged successfully!")
                    except Exception as e:
                        st.error(f"Error logging test: {e}")
                else:
                    st.error("Please fill in both test input and output")
    
    with col2:
        st.subheader("🔧 Debugging Tools")
        
        # Quick prompt comparison
        if st.button("🔍 Compare Last Two Prompts"):
            try:
                from research_logger import get_research_logger
                logger = get_research_logger()
                
                prompt_logs = logger.get_logs(log_type="prompt_test", last_n=2)
                if len(prompt_logs) >= 2:
                    st.write("**Recent Prompt Comparison:**")
                    for i, log in enumerate(prompt_logs[-2:], 1):
                        st.write(f"**Test {i}:**")
                        st.write(f"- Type: {log.get('prompt_type', 'Unknown')}")
                        st.write(f"- Success: {'✅' if log.get('success', True) else '❌'}")
                        st.write(f"- Input: {log.get('input', {}).get('prompt', 'N/A')[:100]}...")
                        st.write("---")
                else:
                    st.info("Need at least 2 prompt tests to compare")
            except Exception as e:
                st.error(f"Error comparing prompts: {e}")
        
        # Show recent errors
        if st.button("⚠️ Show Recent Errors"):
            try:
                from research_logger import get_research_logger
                logger = get_research_logger()
                
                error_logs = [log for log in logger.get_logs(last_n=20) if not log.get('success', True)]
                if error_logs:
                    st.write("**Recent Errors:**")
                    for log in error_logs[-5:]:
                        st.error(f"**{log.get('timestamp', 'Unknown')}:** {log.get('error', 'Unknown error')}")
                        st.caption(f"Type: {log.get('type', 'Unknown')}")
                else:
                    st.success("No recent errors found!")
            except Exception as e:
                st.error(f"Error retrieving errors: {e}")
        
        # Clear current session
        if st.button("🗑️ Clear Current Session"):
            try:
                from research_logger import get_research_logger
                logger = get_research_logger()
                logger.clear_current_session()
                st.success("Current session cleared!")
            except Exception as e:
                st.error(f"Error clearing session: {e}")
    
    # Research tips section
    st.subheader("💡 Tips for Using Research Logs")
    
    with st.expander("🎯 How to Use This for Prompt Engineering"):
        st.write("""
        **For Prompt Engineering:**
        1. **Track Prompt Changes**: Log each prompt version you test
        2. **Compare Performance**: Use the analysis tab to see which prompts work best
        3. **Debug Issues**: Look at error logs to identify common failure patterns
        4. **Monitor API Usage**: Track response times and token usage
        
        **For Evaluation Improvement:**
        1. **Judge Prompt Testing**: Test different judge prompts and compare results
        2. **Scenario Generation**: Track which scenarios produce the best evaluations
        3. **Character Cards**: Compare different character card versions
        4. **Error Analysis**: Identify patterns in failed evaluations
        
        **For Research Insights:**
        1. **Session Comparison**: Compare different research sessions
        2. **Performance Tracking**: Monitor improvements over time
        3. **Statistical Analysis**: Use the analysis tab for quantitative insights
        4. **Debugging**: Quick access to recent errors and issues
        """)
    
    with st.expander("📊 Understanding Log Types"):
        st.write("""
        **Log Types:**
        - **prompt_test**: Individual prompt testing and comparison
        - **api_call**: API requests, responses, and performance metrics
        - **evaluation_result**: Judge evaluations and scoring
        - **comparison_result**: Head-to-head prompt comparisons
        - **error**: Error messages and debugging information
        
        **Key Metrics to Track:**
        - Response time and token usage
        - Success/failure rates
        - Evaluation scores and consistency
        - Error patterns and frequency
        """)
    
    # Export functionality
    st.subheader("📁 Export Research Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Current Session"):
            try:
                from research_logger import get_research_logger
                import json
                
                logger = get_research_logger()
                logs = logger.get_logs()
                
                if logs:
                    # Convert to JSON string
                    json_str = json.dumps(logs, indent=2)
                    st.download_button(
                        label="Download Session Logs",
                        data=json_str,
                        file_name=f"research_session_{logger.get_logs()[0].get('session_id', 'unknown')}.json",
                        mime="application/json"
                    )
                else:
                    st.info("No logs to export in current session")
            except Exception as e:
                st.error(f"Error exporting data: {e}")
    
    with col2:
        if st.button("📈 Generate Research Report"):
            try:
                from research_logger import get_research_logger
                logger = get_research_logger()
                logs = logger.get_logs()
                
                if logs:
                    # Generate a summary report
                    total_logs = len(logs)
                    error_count = len([l for l in logs if not l.get('success', True)])
                    prompt_tests = len([l for l in logs if l['type'] == 'prompt_test'])
                    api_calls = len([l for l in logs if l['type'] == 'api_call'])
                    
                    report = f"""
# Research Session Report

## Session Overview
- **Session ID**: {logs[0].get('session_id', 'Unknown')}
- **Total Logs**: {total_logs}
- **Error Count**: {error_count}
- **Success Rate**: {((total_logs - error_count) / total_logs * 100):.1f}%

## Activity Summary
- **Prompt Tests**: {prompt_tests}
- **API Calls**: {api_calls}
- **Evaluation Results**: {len([l for l in logs if l['type'] == 'evaluation_result'])}
- **Comparisons**: {len([l for l in logs if l['type'] == 'comparison_result'])}

## Recent Activity
{chr(10).join([f"- {log.get('timestamp', 'Unknown')}: {log.get('type', 'Unknown')} - {'✅' if log.get('success', True) else '❌'}" for log in logs[-10:]])}

## Error Summary
{chr(10).join([f"- {log.get('error', 'Unknown error')}" for log in logs if not log.get('success', True)][:5])}
"""
                    
                    st.download_button(
                        label="Download Research Report",
                        data=report,
                        file_name=f"research_report_{logs[0].get('session_id', 'unknown')}.md",
                        mime="text/markdown"
                    )
                else:
                    st.info("No logs to generate report from")
            except Exception as e:
                st.error(f"Error generating report: {e}")


def display_evaluation_dashboard():
    """Display evaluation results dashboard."""
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        import sqlite3
        import pandas as pd
    except ImportError as e:
        st.error(f"Missing required packages: {e}. Please install with: pip install plotly pandas")
        return
    
    # Dashboard mode selection
    dashboard_mode = st.radio(
        "Dashboard Mode",
        ["🎯 Agora Evaluation Pipeline", "📊 Legacy Evaluation Dashboard"],
        help="Choose between the new Agora evaluation pipeline or the legacy dashboard"
    )
    
    if dashboard_mode == "🎯 Agora Evaluation Pipeline":
        # Import and display the new Agora evaluation dashboard
        try:
            from agora_evaluation_dashboard import display_agora_evaluation_dashboard
            display_agora_evaluation_dashboard()
        except ImportError as e:
            st.error(f"Could not load Agora evaluation dashboard: {e}")
            st.info("Falling back to legacy dashboard...")
            display_legacy_evaluation_dashboard()
    else:
        display_legacy_evaluation_dashboard()


def display_legacy_evaluation_dashboard():
    """Display the legacy evaluation results dashboard."""
    
    st.header("🔍 Legacy Evaluation Results Dashboard")
    
    # Overview of available evaluation data
    st.subheader("📊 Available Evaluation Data")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        summary_files = glob("evaluation_results/*/evaluation_summaries.db")
        summary_files.extend(glob("evaluation_data/*/evaluation_results/evaluation_summaries.db"))
        st.metric("Summary Files", len(summary_files))
    
    with col2:
        judgment_files = glob("evaluation_results/*/single_judgments.db")
        judgment_files.extend(glob("evaluation_data/*/evaluation_results/single_judgments.db"))
        st.metric("Single Judgment Files", len(judgment_files))
    
    with col3:
        comparison_files = glob("evaluation_results/*/elo_comparisons.db")
        comparison_files.extend(glob("evaluation_data/*/evaluation_results/elo_comparisons.db"))
        st.metric("ELO Comparison Files", len(comparison_files))
    
    with col4:
        # Check for fine-tuning jobs
        try:
            from fine_tuning_manager import FinetuningManager
            ft_manager = FinetuningManager()
            ft_jobs = ft_manager.list_jobs()
            st.metric("Fine-tuning Jobs", len(ft_jobs))
        except ImportError:
            st.metric("Fine-tuning Jobs", "N/A")
    
    # Evaluation type selection
    st.subheader("📋 Select Evaluation Type")
    eval_type = st.selectbox("Evaluation Type", ["summary", "single", "elo", "fine-tuning"], 
                           help="Summary: Cross-model comparison, Single: Individual conversation analysis, ELO: Comparative rankings, Fine-tuning: Manage fine-tuning jobs")
    
    if eval_type == "summary":
        display_evaluation_summaries()
    elif eval_type == "single":
        display_single_evaluations()
    elif eval_type == "elo":
        display_elo_evaluations()
    elif eval_type == "fine-tuning":
        display_finetuning_interface()


def get_evaluation_config_summary(db_path):
    """Get configuration summary for an evaluation run."""
    import sqlite3
    import json
    
    try:
        # Check if it's an evaluation database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Try to get evaluation configuration
            try:
                cursor.execute("SELECT config_json FROM evaluation_conversations LIMIT 1")
                config_row = cursor.fetchone()
                if config_row:
                    config = json.loads(config_row[0])
                    return {
                        'type': 'Evaluation Database',
                        'model': config.get('model', 'Unknown'),
                        'system_prompt': config.get('system_prompt', 'Unknown')[:100] + '...',
                        'timestamp': config.get('timestamp', 'Unknown'),
                        'ideas_filepath': config.get('ideas_filepath', 'Unknown'),
                        'user_template': config.get('user_message_template', 'Unknown')[:50] + '...'
                    }
            except:
                pass
                
            # Try regular conversation database
            try:
                cursor.execute("SELECT model, system_prompt, created_at FROM conversations LIMIT 1")
                conv_row = cursor.fetchone()
                if conv_row:
                    return {
                        'type': 'Conversation Database',
                        'model': conv_row[0] or 'Unknown',
                        'system_prompt': (conv_row[1] or 'Unknown')[:100] + '...',
                        'created_at': conv_row[2] or 'Unknown',
                        'timestamp': conv_row[2] or 'Unknown'
                    }
            except:
                pass
                
    except Exception as e:
        pass
    
    return {
        'type': 'Unknown Database',
        'model': 'Unknown',
        'system_prompt': 'Unable to read configuration',
        'timestamp': 'Unknown'
    }

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
        import plotly.graph_objects as go
        import plotly.express as px
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
            # Summary statistics with enhanced visualization
            st.subheader("📊 Summary Statistics")
            trait_stats = calculate_trait_statistics(judgments)
            
            # Create two columns for metrics and chart
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.dataframe(trait_stats)
            
            with col2:
                # Create bar chart of average scores
                if not trait_stats.empty:
                    fig = px.bar(
                        trait_stats, 
                        x='Trait', 
                        y='Average Score',
                        title="Average Trait Scores",
                        color='Average Score',
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_layout(
                        xaxis_tickangle=-45,
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Score distribution heatmap
            st.subheader("📈 Score Distribution Heatmap")
            score_matrix = create_score_distribution_matrix(judgments)
            if not score_matrix.empty:
                fig = px.imshow(
                    score_matrix,
                    labels=dict(x="Score", y="Trait", color="Count"),
                    title="Distribution of Scores by Trait",
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Detailed trait analysis
            st.subheader("🔍 Detailed Trait Analysis")
            selected_trait = st.selectbox("Select trait for detailed analysis", trait_stats['Trait'].tolist())
            
            if selected_trait:
                display_trait_detailed_analysis(judgments, selected_trait)
            
            # Evaluation Results Table
            st.subheader("📋 Evaluation Results")
            
            # Create a comprehensive table with all judgments and traits
            evaluation_data = []
            for judgment in judgments:
                conv_id_short = judgment['conversation_id'][:8] + '...'
                
                # Create one row per conversation with all traits as columns
                row = {
                    'Conversation ID': conv_id_short,
                    'Full Conversation ID': judgment['conversation_id']
                }
                
                # Add trait scores as columns
                for tj in judgment['trait_judgments']:
                    row[f"{tj['trait']} Score"] = tj['score']
                
                # Add view button identifier
                row['View'] = f"view_conv_{judgment['conversation_id']}"
                evaluation_data.append(row)
            
            if evaluation_data:
                # Display the main table
                display_df = pd.DataFrame(evaluation_data)
                # Remove the internal columns we don't want to show
                table_df = display_df.drop(['Full Conversation ID', 'View'], axis=1)
                st.dataframe(table_df, use_container_width=True)
                
                # Add view conversation buttons in a row
                st.subheader("👁️ View Full Conversations")
                cols = st.columns(min(len(judgments), 4))
                for i, judgment in enumerate(judgments):
                    with cols[i % 4]:
                        conv_id_short = judgment['conversation_id'][:8]
                        if st.button(f"View {conv_id_short}", key=f"view_conv_{judgment['conversation_id']}"):
                            conversation = load_conversation_details(selected_file, judgment['conversation_id'])
                            if conversation:
                                with st.expander(f"Conversation {conv_id_short} Details", expanded=True):
                                    st.write("**Overall Reasoning:**", judgment['overall_reasoning'])
                                    
                                    # Show trait reasoning in a table with better formatting
                                    trait_reasoning = []
                                    for tj in judgment['trait_judgments']:
                                        trait_reasoning.append({
                                            'Trait': tj['trait'],
                                            'Score': tj['score'],
                                            'Reasoning': tj['reasoning']
                                        })
                                    
                                    if trait_reasoning:
                                        st.subheader("🎯 Trait Evaluations")
                                        df = pd.DataFrame(trait_reasoning)
                                        # Color code the scores
                                        def color_score(val):
                                            if val <= 2:
                                                return 'background-color: #ffcccc'
                                            elif val <= 3:
                                                return 'background-color: #ffffcc'
                                            else:
                                                return 'background-color: #ccffcc'
                                        
                                        styled_df = df.style.applymap(color_score, subset=['Score'])
                                        st.dataframe(styled_df, use_container_width=True)
                                    
                                    st.subheader("💬 Full Conversation")
                                    display_conversation_details(conversation, selected_file)


def display_elo_evaluations():
    """Display ELO evaluation results."""
    try:
        import pandas as pd
    except ImportError as e:
        st.error(f"Missing required packages: {e}")
        return
        
    st.subheader("ELO Evaluation Results")
    
    # Look for ELO comparison files
    comparison_files = glob("evaluation_results/*/elo_comparisons.db")
    comparison_files.extend(glob("evaluation_data/*/evaluation_results/elo_comparisons.db"))
    comparison_files.extend(glob("evaluation_data/*/elo_comparisons.db"))
    comparison_files.extend(glob("evaluation_data/elo_*/elo_comparisons.db"))
    
    if not comparison_files:
        st.warning("No ELO evaluation results found.")
        
        # Add button to run ELO evaluation
        st.subheader("Run ELO Evaluation")
        st.write("Create ELO comparison data by comparing conversations from different database files.")
        
        # Find available database files
        db_files = []
        for path in ["/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/conversations_ui/conversations.db",
                    "/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/conversations_ui/evaluation_data/20250708_195807/hostile_mental_health_response_evaluation.db"]:
            if os.path.exists(path):
                db_files.append(path)
        
        if len(db_files) >= 2:
            if st.button("Run Sample ELO Comparison"):
                st.info("To run ELO comparison, use the command line:\n\n"
                       f"python judge_conversations.py --evaluation-type elo --judge-model anthropic/claude-sonnet-4-20250514 "
                       f"--filepaths {' '.join(db_files[:2])} --traits helpfulness consistency")
        else:
            st.info("Need at least 2 database files for ELO comparison.")
        
        return
    
    selected_file = st.selectbox("Select Comparison File", comparison_files)
    
    if selected_file:
        # Show configuration info for the ELO evaluation
        st.subheader("ELO Evaluation Configuration")
        elo_dir = os.path.dirname(selected_file)
        
        # Look for database files involved in this ELO comparison
        comparisons = load_elo_comparisons_from_db(selected_file)
        
        if comparisons and len(comparisons) > 0:
            # Extract database paths from conversation IDs
            first_comparison = comparisons[0]
            st.write(f"**Judge Model:** {first_comparison.get('judge_model', 'Unknown')}")
            st.write(f"**Traits Evaluated:** {', '.join(set(comp['trait'] for comp in comparisons))}")
            st.write(f"**Total Conversations:** {len(first_comparison.get('conversation_ids', []))}")
            
            # Show link to view configurations
            with st.expander("📋 View Database Configurations"):
                # Try to find original database files
                db_patterns = [
                    "evaluation_data/*/emotional_distress_response_evaluation_benchmark.db",
                    "evaluation_data/*/sensitive_discussion_ethical_response_evaluation.db", 
                    "evaluation_data/*/poetry_feedback_user_interaction_analysis.db"
                ]
                
                for pattern in db_patterns:
                    db_files = glob(pattern)
                    for db_file in db_files:
                        config = get_evaluation_config_summary(db_file)
                        st.write(f"**{os.path.basename(db_file)}**")
                        st.write(f"- Type: {config['type']}")
                        st.write(f"- Model: {config['model']}")
                        st.write(f"- System Prompt: {config['system_prompt']}")
                        st.write(f"- Timestamp: {config['timestamp']}")
                        st.write("---")
        
        if comparisons:
            # Group by trait
            traits = list(set(comp['trait'] for comp in comparisons))
            
            st.subheader("📊 ELO Rankings by Trait")
            for trait in traits:
                trait_comparisons = [comp for comp in comparisons if comp['trait'] == trait]
                
                with st.expander(f"{trait} Rankings", expanded=True):
                    for comparison in trait_comparisons:
                        st.write("**Reasoning:**", comparison['reasoning'])
                        
                        # Create rankings dataframe with conversation viewing
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
                            
                            # Create two columns for table and visualization
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.dataframe(df, use_container_width=True)
                            
                            with col2:
                                # Create bar chart of ELO scores
                                import plotly.express as px
                                fig = px.bar(
                                    df,
                                    x='Rank',
                                    y='Score',
                                    title=f"ELO Scores for {trait}",
                                    color='Score',
                                    color_continuous_scale='RdYlGn'
                                )
                                fig.update_layout(
                                    xaxis_title="Rank",
                                    yaxis_title="ELO Score"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Add buttons to view individual conversations
                            st.write("**👁️ View Individual Conversations:**")
                            cols = st.columns(min(len(comparison['rankings']), 4))
                            for i, ranking in enumerate(comparison['rankings']):
                                with cols[i % 4]:
                                    if st.button(f"View #{ranking['rank']}", key=f"view_elo_{ranking['conversation_id']}_{trait}"):
                                        conversation = load_conversation_details(selected_file, ranking['conversation_id'])
                                        if conversation:
                                            with st.expander(f"Conversation #{ranking['rank']} Details", expanded=True):
                                                # Show ELO score prominently
                                                st.metric(f"ELO Score for {trait}", f"{ranking['score']:.1f}", f"Rank: {ranking['rank']}")
                                                display_conversation_details(conversation, selected_file)


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
                            st.metric("Average Score", f"{trait_summary.get('average_score', 0):.2f}")
                            st.metric("Std Deviation", f"{trait_summary.get('std_deviation', 0):.2f}")
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
            'Average Score': round(sum(scores) / len(scores), 2),
            'Min Score': min(scores),
            'Max Score': max(scores),
            'Count': len(scores)
        })
    
    return pd.DataFrame(stats)


def create_score_distribution_matrix(judgments):
    """Create a matrix showing score distribution by trait for heatmap visualization."""
    import pandas as pd
    
    # Create a matrix where rows are traits and columns are scores (1-5)
    traits = set()
    for judgment in judgments:
        for tj in judgment.get('trait_judgments', []):
            traits.add(tj['trait'])
    
    if not traits:
        return pd.DataFrame()
    
    # Initialize matrix
    matrix_data = []
    for trait in sorted(traits):
        score_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for judgment in judgments:
            for tj in judgment.get('trait_judgments', []):
                if tj['trait'] == trait:
                    score_counts[tj['score']] += 1
        
        matrix_data.append([score_counts[1], score_counts[2], score_counts[3], score_counts[4], score_counts[5]])
    
    return pd.DataFrame(matrix_data, index=sorted(traits), columns=['1', '2', '3', '4', '5'])


def display_trait_detailed_analysis(judgments, trait):
    """Display detailed analysis for a specific trait."""
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    
    # Collect all data for this trait
    trait_data = []
    for judgment in judgments:
        for tj in judgment.get('trait_judgments', []):
            if tj['trait'] == trait:
                trait_data.append({
                    'Conversation ID': judgment['conversation_id'][:8] + '...',
                    'Score': tj['score'],
                    'Reasoning': tj['reasoning']
                })
    
    if not trait_data:
        st.warning(f"No data found for trait: {trait}")
        return
    
    # Create columns for visualization
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Score distribution pie chart
        df = pd.DataFrame(trait_data)
        score_counts = df['Score'].value_counts().sort_index()
        
        fig = px.pie(
            values=score_counts.values,
            names=score_counts.index,
            title=f"Score Distribution for {trait}",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Score timeline/histogram
        fig = px.histogram(
            df,
            x='Score',
            nbins=5,
            title=f"Score Frequency for {trait}",
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(
            xaxis_title="Score",
            yaxis_title="Frequency",
            bargap=0.1
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table with reasoning
    st.subheader(f"Detailed Scores and Reasoning for {trait}")
    
    # Color code the dataframe
    def color_score_detailed(val):
        if val <= 2:
            return 'background-color: #ffcccc'
        elif val <= 3:
            return 'background-color: #ffffcc'
        else:
            return 'background-color: #ccffcc'
    
    styled_df = df.style.applymap(color_score_detailed, subset=['Score'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Summary statistics for this trait
    st.subheader(f"Summary Statistics for {trait}")
    col1, col2, col3, col4 = st.columns(4)
    
    scores = [item['Score'] for item in trait_data]
    with col1:
        st.metric("Average Score", f"{sum(scores)/len(scores):.2f}")
    with col2:
        st.metric("Min Score", min(scores))
    with col3:
        st.metric("Max Score", max(scores))
    with col4:
        st.metric("Total Evaluations", len(scores))


def load_conversation_details(db_path: str, conversation_id: str) -> Dict:
    """Load full conversation details for display."""
    import sqlite3
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # First try evaluation_conversations table
            cursor.execute("""
                SELECT ec.*, ei.text as idea_text, ect.content as context_content
                FROM evaluation_conversations ec
                LEFT JOIN evaluation_ideas ei ON ec.idea_id = ei.id
                LEFT JOIN evaluation_contexts ect ON ec.context_id = ect.id
                WHERE ec.id = ?
            """, (conversation_id,))
            
            conversation = cursor.fetchone()
            if conversation:
                conversation = dict(conversation)
                
                # Load messages
                cursor.execute("""
                    SELECT * FROM messages 
                    WHERE conversation_id = ? 
                    ORDER BY message_index
                """, (conversation_id,))
                
                messages = [dict(row) for row in cursor.fetchall()]
                conversation['messages'] = messages
                
                # Parse config if available
                if conversation.get('config_json'):
                    import json
                    try:
                        conversation['config'] = json.loads(conversation['config_json'])
                    except json.JSONDecodeError:
                        conversation['config'] = {}
                
                return conversation
            
            # Fallback to regular conversations table
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            conversation = cursor.fetchone()
            if conversation:
                conversation = dict(conversation)
                cursor.execute("""
                    SELECT * FROM messages 
                    WHERE conversation_id = ? 
                    ORDER BY message_index
                """, (conversation_id,))
                messages = [dict(row) for row in cursor.fetchall()]
                conversation['messages'] = messages
                return conversation
                
    except sqlite3.Error as e:
        st.error(f"Error loading conversation from {db_path}: {e}")
    
    return None


def display_conversation_details(conversation: Dict, db_path: str):
    """Display full conversation details in the UI."""
    if not conversation:
        st.error("Conversation not found")
        return
    
    # Conversation metadata
    st.subheader("Conversation Details")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Conversation ID:**", conversation['id'][:16] + "...")
        st.write("**Created:**", conversation.get('created_at', 'Unknown'))
        if conversation.get('config'):
            st.write("**Model:**", conversation['config'].get('model', 'Unknown'))
    
    with col2:
        if conversation.get('idea_text'):
            st.write("**Evaluation Idea:**", conversation['idea_text'][:100] + "...")
        if conversation.get('name'):
            st.write("**Name:**", conversation['name'])
        if conversation.get('system_prompt_name'):
            st.write("**Persona:**", conversation['system_prompt_name'])
    
    # System prompt
    if conversation.get('system_prompt'):
        with st.expander("System Prompt"):
            st.text_area("", conversation['system_prompt'], height=150, disabled=True)
    
    # Context (for evaluation conversations)
    if conversation.get('context_content'):
        with st.expander("Evaluation Context"):
            st.text_area("", conversation['context_content'], height=200, disabled=True)
    
    # Messages
    st.subheader("Conversation Messages")
    for msg in conversation.get('messages', []):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        
        if role == 'user':
            st.chat_message("user").write(content)
        elif role == 'assistant':
            st.chat_message("assistant").write(content)
        else:
            st.chat_message("system").write(content)


def display_finetuning_interface():
    """Display fine-tuning management interface."""
    st.header("🤖 Fine-tuning Management")
    
    try:
        from fine_tuning_manager import FinetuningManager, FinetuningStatus
        import asyncio
        import pandas as pd
    except ImportError as e:
        st.error(f"Fine-tuning manager not available: {e}")
        return
    
    # Initialize fine-tuning manager
    ft_manager = FinetuningManager()
    
    # Create tabs for different fine-tuning operations
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Job Management", "🚀 Create New Job", "📊 Statistics", "📝 Data Preparation"])
    
    with tab1:
        st.subheader("Fine-tuning Jobs")
        
        # Filter controls
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", 
                                       ["all", "pending", "running", "completed", "failed", "cancelled"])
        with col2:
            provider_filter = st.selectbox("Filter by Provider", ["all", "openai", "together"])
        with col3:
            if st.button("🔄 Refresh Jobs"):
                st.rerun()
        
        # Load jobs with filters
        jobs = ft_manager.list_jobs(
            status=status_filter if status_filter != "all" else None,
            provider=provider_filter if provider_filter != "all" else None
        )
        
        if jobs:
            # Display jobs in a table
            job_data = []
            for job in jobs:
                job_data.append({
                    "ID": job.id[:8] + "...",
                    "Name": job.name,
                    "Provider": job.provider,
                    "Model": job.model,
                    "Status": job.status,
                    "Created": job.created_at[:10],
                    "Fine-tuned Model": job.fine_tuned_model or "N/A"
                })
            
            df = pd.DataFrame(job_data)
            st.dataframe(df, use_container_width=True)
            
            # Job details and actions
            st.subheader("Job Details & Actions")
            job_ids = {f"{job.name} ({job.id[:8]}...)": job.id for job in jobs}
            selected_job_key = st.selectbox("Select Job", list(job_ids.keys()))
            
            if selected_job_key:
                selected_job_id = job_ids[selected_job_key]
                selected_job = ft_manager.get_job(selected_job_id)
                
                if selected_job:
                    # Job details
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Job Information:**")
                        st.write(f"- ID: {selected_job.id}")
                        st.write(f"- Name: {selected_job.name}")
                        st.write(f"- Provider: {selected_job.provider}")
                        st.write(f"- Model: {selected_job.model}")
                        st.write(f"- Status: {selected_job.status}")
                        st.write(f"- Created: {selected_job.created_at}")
                        
                        if selected_job.fine_tuned_model:
                            st.write(f"- Fine-tuned Model: {selected_job.fine_tuned_model}")
                            
                            # Add to model list for testing
                            if st.button("🧪 Test Fine-tuned Model"):
                                st.session_state.model_1 = selected_job.fine_tuned_model
                                st.success(f"Set model to: {selected_job.fine_tuned_model}")
                                st.info("Switch to the Chat Interface tab to test the model!")
                    
                    with col2:
                        st.write("**Configuration:**")
                        st.json(selected_job.config)
                        
                        if selected_job.metrics:
                            st.write("**Metrics:**")
                            st.json(selected_job.metrics)
                    
                    # Actions
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    with action_col1:
                        if selected_job.status == FinetuningStatus.PENDING.value:
                            if st.button("🚀 Run Job"):
                                with st.spinner("Running fine-tuning job..."):
                                    try:
                                        result = asyncio.run(ft_manager.run_job(selected_job.id))
                                        if result.status == FinetuningStatus.COMPLETED.value:
                                            st.success("Job completed successfully!")
                                            st.write(f"Fine-tuned model: {result.fine_tuned_model}")
                                        else:
                                            st.error(f"Job failed: {result.error_message}")
                                    except Exception as e:
                                        st.error(f"Error running job: {e}")
                                    st.rerun()
                    
                    with action_col2:
                        if selected_job.status == FinetuningStatus.RUNNING.value:
                            if st.button("🛑 Cancel Job"):
                                if ft_manager.cancel_job(selected_job.id):
                                    st.success("Job cancelled")
                                    st.rerun()
                                else:
                                    st.error("Failed to cancel job")
                    
                    with action_col3:
                        if st.button("🗑️ Delete Job"):
                            if ft_manager.delete_job(selected_job.id):
                                st.success("Job deleted")
                                st.rerun()
                            else:
                                st.error("Failed to delete job")
                    
                    # Error details
                    if selected_job.error_message:
                        st.error(f"**Error:** {selected_job.error_message}")
                    
                    # Logs
                    if selected_job.logs:
                        with st.expander("📝 Logs"):
                            for log in selected_job.logs:
                                st.text(log)
        else:
            st.info("No fine-tuning jobs found.")
    
    with tab2:
        st.subheader("Create New Fine-tuning Job")
        
        # Job creation form
        with st.form("create_job_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                job_name = st.text_input("Job Name", help="Descriptive name for the job")
                provider = st.selectbox("Provider", ["openai", "together"])
                
                # Get available models
                available_models = ft_manager.get_available_models()
                model_options = available_models.get(provider, [])
                base_model = st.selectbox("Base Model", model_options)
                
                train_file = st.text_input("Training Data File", 
                                         help="Path to training data file (JSONL format)")
                val_file = st.text_input("Validation Data File (Optional)", 
                                       help="Path to validation data file (JSONL format)")
            
            with col2:
                n_epochs = st.number_input("Number of Epochs", min_value=1, max_value=10, value=1)
                
                if provider == "openai":
                    batch_size = st.text_input("Batch Size", value="auto", 
                                             help="Batch size or 'auto'")
                    learning_rate = st.text_input("Learning Rate Multiplier", value="auto",
                                                help="Learning rate multiplier or 'auto'")
                else:  # together
                    batch_size = st.number_input("Batch Size", min_value=1, max_value=32, value=8)
                    learning_rate = st.number_input("Learning Rate", min_value=0.00001, max_value=0.001, 
                                                  value=0.00001, format="%.5f")
                    lora_r = st.number_input("LoRA R", min_value=1, max_value=256, value=64)
                
                wandb_project = st.text_input("W&B Project (Optional)", 
                                            help="Weights & Biases project name")
            
            submitted = st.form_submit_button("Create Job")
            
            if submitted:
                if not job_name or not train_file:
                    st.error("Job name and training file are required")
                else:
                    try:
                        if provider == "openai":
                            # Convert string values for OpenAI
                            batch_size_val = batch_size if batch_size == "auto" else int(batch_size)
                            learning_rate_val = learning_rate if learning_rate == "auto" else float(learning_rate)
                            
                            job = ft_manager.create_openai_job(
                                name=job_name,
                                model=base_model,
                                train_file=train_file,
                                val_file=val_file if val_file else None,
                                n_epochs=n_epochs,
                                batch_size=batch_size_val,
                                learning_rate_multiplier=learning_rate_val,
                                wandb_project_name=wandb_project if wandb_project else None
                            )
                        else:  # together
                            job = ft_manager.create_together_job(
                                name=job_name,
                                model=base_model,
                                train_file=train_file,
                                val_file=val_file if val_file else None,
                                n_epochs=n_epochs,
                                batch_size=int(batch_size),
                                learning_rate=learning_rate,
                                lora_r=lora_r,
                                wandb_project_name=wandb_project if wandb_project else None
                            )
                        
                        st.success(f"Job created successfully! ID: {job.id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating job: {e}")
    
    with tab3:
        st.subheader("Fine-tuning Statistics")
        
        stats = ft_manager.get_job_stats()
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Jobs", stats['total_jobs'])
        with col2:
            st.metric("Completed Jobs", stats['completed_jobs'])
        with col3:
            st.metric("Failed Jobs", stats['failed_jobs'])
        with col4:
            success_rate = (stats['completed_jobs'] / stats['total_jobs'] * 100) if stats['total_jobs'] > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Charts
        if stats['total_jobs'] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                # Status distribution
                status_data = stats['by_status']
                if status_data:
                    import plotly.express as px
                    fig = px.pie(
                        values=list(status_data.values()),
                        names=list(status_data.keys()),
                        title="Jobs by Status"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Provider distribution
                provider_data = stats['by_provider']
                if provider_data:
                    fig = px.bar(
                        x=list(provider_data.keys()),
                        y=list(provider_data.values()),
                        title="Jobs by Provider"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Model usage
            st.subheader("Model Usage")
            model_data = stats['by_model']
            if model_data:
                df = pd.DataFrame(list(model_data.items()), columns=['Model', 'Jobs'])
                st.dataframe(df, use_container_width=True)
    
    with tab4:
        st.subheader("Data Preparation")
        
        st.write("Convert conversation databases to fine-tuning format (JSONL)")
        
        # Database selection
        available_dbs = get_available_databases()
        selected_db_name = st.selectbox("Select Conversation Database", list(available_dbs.keys()))
        selected_db_path = available_dbs[selected_db_name]
        
        # Configuration
        col1, col2 = st.columns(2)
        
        with col1:
            output_filename = st.text_input("Output Filename", value="fine_tuning_data.jsonl")
            max_conversations = st.number_input("Max Conversations (0 = all)", min_value=0, value=0)
            
        with col2:
            system_prompt_override = st.text_area("System Prompt Override (optional)", 
                                                height=100,
                                                help="Override system prompt for all conversations")
        
        # Preview database info
        if st.button("📊 Preview Database Info"):
            try:
                import sqlite3
                with sqlite3.connect(selected_db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get conversation count
                    cursor.execute("SELECT COUNT(*) FROM conversations")
                    conv_count = cursor.fetchone()[0]
                    
                    # Get sample system prompts
                    cursor.execute("SELECT DISTINCT system_prompt_name FROM conversations WHERE system_prompt_name IS NOT NULL LIMIT 5")
                    personas = [row[0] for row in cursor.fetchall()]
                    
                    # Get sample models
                    cursor.execute("SELECT DISTINCT model FROM conversations WHERE model IS NOT NULL LIMIT 5")
                    models = [row[0] for row in cursor.fetchall()]
                    
                    st.write(f"**Conversations:** {conv_count}")
                    st.write(f"**Personas:** {', '.join(personas) if personas else 'None'}")
                    st.write(f"**Models:** {', '.join(models) if models else 'None'}")
                    
            except Exception as e:
                st.error(f"Error reading database: {e}")
        
        # Generate training data
        if st.button("🚀 Generate Training Data"):
            if not output_filename:
                st.error("Please specify an output filename")
            else:
                with st.spinner("Generating training data..."):
                    try:
                        result = ft_manager.generate_finetuning_data_from_conversations(
                            selected_db_path,
                            output_filename,
                            system_prompt_override if system_prompt_override else None,
                            max_conversations if max_conversations > 0 else None
                        )
                        
                        st.success(result)
                        st.info(f"Training data saved to: {output_filename}")
                        
                        # Show preview of generated data
                        if os.path.exists(output_filename):
                            with open(output_filename, 'r') as f:
                                lines = f.readlines()[:3]  # Show first 3 examples
                                
                            st.subheader("Preview of Generated Data")
                            for i, line in enumerate(lines, 1):
                                with st.expander(f"Example {i}"):
                                    try:
                                        example = json.loads(line)
                                        st.json(example)
                                    except json.JSONDecodeError:
                                        st.error(f"Invalid JSON in line {i}")
                                        
                    except Exception as e:
                        st.error(f"Error generating training data: {e}")
        
        # Help section
        with st.expander("ℹ️ Help: Fine-tuning Data Format"):
            st.write("""
            **Fine-tuning Data Format:**
            
            The generated JSONL file contains training examples in the format:
            ```json
            {
                "messages": [
                    {"role": "system", "content": "System prompt..."},
                    {"role": "user", "content": "User message..."},
                    {"role": "assistant", "content": "Assistant response..."}
                ]
            }
            ```
            
            **Tips:**
            - Use conversations with good examples of your desired behavior
            - Include diverse examples to improve model generalization
            - System prompt override can standardize behavior across conversations
            - Start with 50-100 examples for initial testing
            """)
        
        # File management
        st.subheader("📁 Training Data Files")
        
        # List existing JSONL files
        jsonl_files = glob("*.jsonl")
        if jsonl_files:
            st.write("**Available Training Files:**")
            for file in jsonl_files:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(file)
                with col2:
                    # File size
                    size = os.path.getsize(file) / 1024  # KB
                    st.text(f"{size:.1f} KB")
                with col3:
                    if st.button("🗑️", key=f"delete_{file}"):
                        os.remove(file)
                        st.rerun()
        else:
            st.info("No training data files found in current directory")


def get_available_models_with_finetuned():
    """Get available models including fine-tuned models."""
    models = list(ALL_MODELS)  # Start with base models
    
    try:
        from fine_tuning_manager import FinetuningManager, FinetuningStatus
        ft_manager = FinetuningManager()
        
        # Get completed fine-tuning jobs
        completed_jobs = ft_manager.list_jobs(status=FinetuningStatus.COMPLETED.value)
        
        # Add fine-tuned models to the list
        for job in completed_jobs:
            if job.fine_tuned_model:
                models.append(f"ft:{job.fine_tuned_model}")
        
    except ImportError:
        pass  # Fine-tuning not available
    
    return models


if __name__ == "__main__":
    main()