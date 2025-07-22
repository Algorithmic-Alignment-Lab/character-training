#!/usr/bin/env python3
"""
Research Logger
===============

Comprehensive logging system for researchers to track and analyze prompt performance.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import streamlit as st


class ResearchLogger:
    """
    Advanced logging system for prompt research and debugging.
    
    Tracks:
    - Prompt inputs and outputs
    - API calls and responses
    - Error messages and failures
    - Performance metrics
    - Comparison results
    """
    
    def __init__(self, log_dir: str = "research_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize session state for logs
        if 'research_logs' not in st.session_state:
            st.session_state.research_logs = []
        if 'current_session' not in st.session_state:
            st.session_state.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        if 'current_evaluation' not in st.session_state:
            st.session_state.current_evaluation = None
    
    def log_prompt_test(self, prompt_type: str, prompt_version: str, 
                       input_data: Dict[str, Any], output_data: Dict[str, Any],
                       performance_metrics: Dict[str, Any] = None):
        """Log a prompt test with full details."""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.current_session,
            'evaluation_id': st.session_state.current_evaluation['id'] if st.session_state.current_evaluation else None,
            'type': 'prompt_test',
            'prompt_type': prompt_type,
            'prompt_version': prompt_version,
            'input': input_data,
            'output': output_data,
            'performance': performance_metrics or {},
            'success': output_data.get('success', True),
            'error': output_data.get('error', None)
        }
        
        # Add to session state
        st.session_state.research_logs.append(log_entry)
        
        # Save to file
        self._save_log_entry(log_entry)
        
        return log_entry
    
    def log_api_call(self, endpoint: str, prompt: str, response: str,
                    model: str, tokens_used: int = None, response_time: float = None,
                    error: str = None, system_prompt: str = None, 
                    conversation_context: dict = None, prompt_type: str = None):
        """Log an API call with full details including system prompts."""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.current_session,
            'evaluation_id': st.session_state.current_evaluation['id'] if st.session_state.current_evaluation else None,
            'type': 'api_call',
            'endpoint': endpoint,
            'model': model,
            'prompt': prompt,
            'response': response,
            'system_prompt': system_prompt,
            'conversation_context': conversation_context,
            'prompt_type': prompt_type,
            'tokens_used': tokens_used,
            'response_time': response_time,
            'success': error is None,
            'error': error
        }
        
        st.session_state.research_logs.append(log_entry)
        self._save_log_entry(log_entry)
        
        return log_entry
    
    def log_llm_generation(self, generation_type: str, system_prompt: str, 
                          user_prompt: str, model_response: str, model: str,
                          tokens_used: int = None, response_time: float = None,
                          context: dict = None, error: str = None):
        """Log LLM generation with full prompt details."""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.current_session,
            'evaluation_id': st.session_state.current_evaluation['id'] if st.session_state.current_evaluation else None,
            'type': 'llm_generation',
            'generation_type': generation_type,
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'model_response': model_response,
            'model': model,
            'tokens_used': tokens_used,
            'response_time': response_time,
            'context': context or {},
            'success': error is None,
            'error': error
        }
        
        st.session_state.research_logs.append(log_entry)
        self._save_log_entry(log_entry)
        
        return log_entry
    
    def log_evaluation_result(self, evaluation_type: str, conversation_id: str,
                             judge_prompt: str, judge_response: str,
                             scores: Dict[str, float], reasoning: str,
                             error: str = None):
        """Log an evaluation result with full details."""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.current_session,
            'type': 'evaluation_result',
            'evaluation_type': evaluation_type,
            'conversation_id': conversation_id,
            'judge_prompt': judge_prompt,
            'judge_response': judge_response,
            'scores': scores,
            'reasoning': reasoning,
            'success': error is None,
            'error': error
        }
        
        st.session_state.research_logs.append(log_entry)
        self._save_log_entry(log_entry)
        
        return log_entry
    
    def log_comparison_result(self, comparison_type: str, prompt_versions: List[str],
                             test_input: str, outputs: Dict[str, str],
                             winner: str, reasoning: str):
        """Log a comparison result between prompt versions."""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.current_session,
            'type': 'comparison_result',
            'comparison_type': comparison_type,
            'prompt_versions': prompt_versions,
            'test_input': test_input,
            'outputs': outputs,
            'winner': winner,
            'reasoning': reasoning,
            'success': True
        }
        
        st.session_state.research_logs.append(log_entry)
        self._save_log_entry(log_entry)
        
        return log_entry
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any]):
        """Log an error with context."""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.current_session,
            'type': 'error',
            'error_type': error_type,
            'error_message': error_message,
            'context': context,
            'success': False
        }
        
        st.session_state.research_logs.append(log_entry)
        self._save_log_entry(log_entry)
        
        return log_entry
    
    def start_evaluation_session(self, evaluation_id: str, evaluation_type: str, 
                                config: Dict[str, Any] = None):
        """Start a new evaluation session for better log correlation."""
        
        st.session_state.current_evaluation = {
            'id': evaluation_id,
            'type': evaluation_type,
            'config': config or {},
            'start_time': datetime.now().isoformat(),
            'logs': []
        }
        
        # Log the evaluation start
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.current_session,
            'evaluation_id': evaluation_id,
            'type': 'evaluation_start',
            'evaluation_type': evaluation_type,
            'config': config or {},
            'success': True
        }
        
        st.session_state.research_logs.append(log_entry)
        self._save_log_entry(log_entry)
        
        return log_entry
    
    def end_evaluation_session(self, success: bool = True, summary: Dict[str, Any] = None):
        """End the current evaluation session."""
        
        if not st.session_state.current_evaluation:
            return None
        
        evaluation_id = st.session_state.current_evaluation['id']
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.current_session,
            'evaluation_id': evaluation_id,
            'type': 'evaluation_end',
            'success': success,
            'summary': summary or {},
            'duration': self._calculate_evaluation_duration()
        }
        
        st.session_state.research_logs.append(log_entry)
        self._save_log_entry(log_entry)
        
        # Clear current evaluation
        st.session_state.current_evaluation = None
        
        return log_entry
    
    def _calculate_evaluation_duration(self) -> float:
        """Calculate duration of current evaluation session."""
        
        if not st.session_state.current_evaluation:
            return 0.0
        
        try:
            start_time = datetime.fromisoformat(st.session_state.current_evaluation['start_time'])
            end_time = datetime.now()
            return (end_time - start_time).total_seconds()
        except:
            return 0.0
    
    def _save_log_entry(self, log_entry: Dict[str, Any]):
        """Save log entry to file."""
        
        session_file = os.path.join(self.log_dir, f"session_{st.session_state.current_session}.jsonl")
        
        with open(session_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_logs(self, log_type: str = None, last_n: int = None) -> List[Dict[str, Any]]:
        """Get logs with optional filtering."""
        
        logs = st.session_state.research_logs
        
        if log_type:
            logs = [log for log in logs if log['type'] == log_type]
        
        if last_n:
            logs = logs[-last_n:]
        
        return logs
    
    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific session."""
        
        session_file = os.path.join(self.log_dir, f"session_{session_id}.jsonl")
        
        if not os.path.exists(session_file):
            return []
        
        logs = []
        with open(session_file, 'r') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return logs
    
    def get_available_sessions(self) -> List[str]:
        """Get list of available log sessions."""
        
        sessions = []
        for file in os.listdir(self.log_dir):
            if file.startswith("session_") and file.endswith(".jsonl"):
                session_id = file.replace("session_", "").replace(".jsonl", "")
                sessions.append(session_id)
        
        return sorted(sessions, reverse=True)
    
    def clear_current_session(self):
        """Clear current session logs."""
        
        st.session_state.research_logs = []
        st.session_state.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")


def display_research_logs():
    """Display comprehensive research logs for debugging."""
    
    st.subheader("🔍 Research Logs & Debugging")
    
    logger = ResearchLogger()
    
    # Session selection
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        sessions = logger.get_available_sessions()
        if sessions:
            selected_session = st.selectbox("Select Session", sessions)
        else:
            selected_session = st.session_state.current_session
            st.info(f"Current session: {selected_session}")
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Current"):
            logger.clear_current_session()
            st.rerun()
    
    # Get logs for selected session
    if selected_session == st.session_state.current_session:
        logs = logger.get_logs()
    else:
        logs = logger.get_session_logs(selected_session)
    
    if not logs:
        st.info("No logs available for this session. Run some tests to generate logs.")
        return
    
    # Log filtering
    st.subheader("📊 Log Overview")
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_logs = len(logs)
        st.metric("Total Logs", total_logs)
    
    with col2:
        error_logs = len([log for log in logs if not log.get('success', True)])
        st.metric("Errors", error_logs)
    
    with col3:
        prompt_tests = len([log for log in logs if log['type'] == 'prompt_test'])
        st.metric("Prompt Tests", prompt_tests)
    
    with col4:
        api_calls = len([log for log in logs if log['type'] == 'api_call'])
        st.metric("API Calls", api_calls)
    
    # Log filtering options
    st.subheader("🔍 Filter Logs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_types = ['all'] + list(set([log['type'] for log in logs]))
        selected_type = st.selectbox("Log Type", log_types)
    
    with col2:
        show_errors_only = st.checkbox("Show Errors Only")
    
    with col3:
        last_n = st.number_input("Show Last N Logs", min_value=1, max_value=len(logs), value=min(50, len(logs)))
    
    # Filter logs
    filtered_logs = logs
    
    if selected_type != 'all':
        filtered_logs = [log for log in filtered_logs if log['type'] == selected_type]
    
    if show_errors_only:
        filtered_logs = [log for log in filtered_logs if not log.get('success', True)]
    
    filtered_logs = filtered_logs[-last_n:]
    
    # Display logs
    st.subheader(f"📋 Logs ({len(filtered_logs)} entries)")
    
    for i, log in enumerate(reversed(filtered_logs)):
        display_log_entry(log, i)


def display_log_entry(log: Dict[str, Any], index: int):
    """Display a single log entry with full details."""
    
    # Determine log level styling
    if not log.get('success', True):
        border_color = "#ff4444"
        bg_color = "#ffeeee"
        icon = "❌"
    elif log['type'] == 'error':
        border_color = "#ff4444"
        bg_color = "#ffeeee"
        icon = "❌"
    elif log['type'] == 'prompt_test':
        border_color = "#4444ff"
        bg_color = "#eeeeff"
        icon = "🧪"
    elif log['type'] == 'api_call':
        border_color = "#44ff44"
        bg_color = "#eeffee"
        icon = "🔗"
    elif log['type'] == 'llm_generation':
        border_color = "#aa44ff"
        bg_color = "#f8eeff"
        icon = "🤖"
    elif log['type'] == 'evaluation_result':
        border_color = "#ffaa44"
        bg_color = "#fff8ee"
        icon = "⚖️"
    else:
        border_color = "#888888"
        bg_color = "#f8f8f8"
        icon = "📝"
    
    # Create expandable log entry
    timestamp = datetime.fromisoformat(log['timestamp']).strftime("%H:%M:%S")
    title = f"{icon} {timestamp} - {log['type'].replace('_', ' ').title()}"
    
    if log.get('error'):
        title += f" - ERROR: {log['error']}"
    
    with st.expander(title, expanded=False):
        
        # Basic info
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Type:** {log['type']}")
            st.write(f"**Time:** {log['timestamp']}")
            st.write(f"**Success:** {'✅' if log.get('success', True) else '❌'}")
        
        with col2:
            st.write(f"**Session:** {log['session_id']}")
            if log.get('error'):
                st.error(f"**Error:** {log['error']}")
        
        # Type-specific details
        if log['type'] == 'prompt_test':
            display_prompt_test_details(log)
        elif log['type'] == 'api_call':
            display_api_call_details(log)
        elif log['type'] == 'llm_generation':
            display_llm_generation_details(log)
        elif log['type'] == 'evaluation_result':
            display_evaluation_details(log)
        elif log['type'] == 'comparison_result':
            display_comparison_details(log)
        elif log['type'] == 'error':
            display_error_details(log)
        
        # Raw log data
        with st.expander("📄 Raw Log Data"):
            st.json(log)


def display_prompt_test_details(log: Dict[str, Any]):
    """Display details for prompt test logs."""
    
    st.subheader("🧪 Prompt Test Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Prompt Type:** {log['prompt_type']}")
        st.write(f"**Version:** {log['prompt_version']}")
    
    with col2:
        if log.get('performance'):
            perf = log['performance']
            if 'response_time' in perf:
                st.write(f"**Response Time:** {perf['response_time']:.2f}s")
            if 'tokens_used' in perf:
                st.write(f"**Tokens Used:** {perf['tokens_used']}")
    
    # Input data
    st.subheader("📥 Input")
    if log.get('input'):
        if isinstance(log['input'], dict) and 'prompt' in log['input']:
            st.text_area("Prompt", log['input']['prompt'], height=200, disabled=True)
        else:
            st.json(log['input'])
    
    # Output data
    st.subheader("📤 Output")
    if log.get('output'):
        if isinstance(log['output'], dict) and 'response' in log['output']:
            st.text_area("Response", log['output']['response'], height=200, disabled=True)
        else:
            st.json(log['output'])


def display_api_call_details(log: Dict[str, Any]):
    """Display details for API call logs."""
    
    st.subheader("🔗 API Call Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Endpoint:** {log['endpoint']}")
        st.write(f"**Model:** {log['model']}")
        if log.get('prompt_type'):
            st.write(f"**Prompt Type:** {log['prompt_type']}")
    
    with col2:
        if log.get('tokens_used'):
            st.write(f"**Tokens Used:** {log['tokens_used']}")
        if log.get('response_time'):
            st.write(f"**Response Time:** {log['response_time']:.2f}s")
    
    # System Prompt (if available)
    if log.get('system_prompt'):
        st.subheader("🎯 System Prompt")
        st.text_area("System Prompt", log['system_prompt'], height=200, disabled=True, key=f"system_{log.get('timestamp', 'unknown')}")
    
    # User Prompt
    st.subheader("📝 User Prompt")
    st.text_area("User Prompt", log['prompt'], height=200, disabled=True, key=f"user_{log.get('timestamp', 'unknown')}")
    
    # Response
    st.subheader("📤 Model Response")
    st.text_area("Model Response", log['response'], height=200, disabled=True, key=f"response_{log.get('timestamp', 'unknown')}")
    
    # Conversation Context (if available)
    if log.get('conversation_context'):
        st.subheader("💬 Conversation Context")
        st.json(log['conversation_context'])


def display_llm_generation_details(log: Dict[str, Any]):
    """Display details for LLM generation logs."""
    
    st.subheader("🤖 LLM Generation Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Generation Type:** {log['generation_type']}")
        st.write(f"**Model:** {log['model']}")
    
    with col2:
        if log.get('tokens_used'):
            st.write(f"**Tokens Used:** {log['tokens_used']}")
        if log.get('response_time'):
            st.write(f"**Response Time:** {log['response_time']:.2f}s")
    
    # System Prompt
    st.subheader("🎯 System Prompt")
    st.text_area("System Prompt", log['system_prompt'], height=200, disabled=True, key=f"llm_system_{log.get('timestamp', 'unknown')}")
    
    # User Prompt
    st.subheader("📝 User Prompt")
    st.text_area("User Prompt", log['user_prompt'], height=200, disabled=True, key=f"llm_user_{log.get('timestamp', 'unknown')}")
    
    # Model Response
    st.subheader("📤 Model Response")
    st.text_area("Model Response", log['model_response'], height=200, disabled=True, key=f"llm_response_{log.get('timestamp', 'unknown')}")
    
    # Context
    if log.get('context'):
        st.subheader("🔍 Generation Context")
        st.json(log['context'])


def display_evaluation_details(log: Dict[str, Any]):
    """Display details for evaluation logs."""
    
    st.subheader("⚖️ Evaluation Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Evaluation Type:** {log['evaluation_type']}")
        st.write(f"**Conversation ID:** {log['conversation_id']}")
    
    with col2:
        if log.get('scores'):
            st.write("**Scores:**")
            for trait, score in log['scores'].items():
                st.write(f"  - {trait}: {score}")
    
    # Judge prompt
    st.subheader("👨‍⚖️ Judge Prompt")
    st.text_area("Judge Prompt", log['judge_prompt'], height=200, disabled=True)
    
    # Judge response
    st.subheader("🗣️ Judge Response")
    st.text_area("Judge Response", log['judge_response'], height=200, disabled=True)
    
    # Reasoning
    if log.get('reasoning'):
        st.subheader("💭 Reasoning")
        st.text_area("Evaluation Reasoning", log['reasoning'], height=100, disabled=True)


def display_comparison_details(log: Dict[str, Any]):
    """Display details for comparison logs."""
    
    st.subheader("🔍 Comparison Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Comparison Type:** {log['comparison_type']}")
        st.write(f"**Winner:** {log['winner']}")
    
    with col2:
        st.write(f"**Versions Compared:** {', '.join(log['prompt_versions'])}")
    
    # Test input
    st.subheader("📥 Test Input")
    st.text_area("Test Input", log['test_input'], height=100, disabled=True)
    
    # Outputs
    st.subheader("📤 Outputs")
    for version, output in log['outputs'].items():
        st.write(f"**{version}:**")
        st.text_area(f"Output - {version}", output, height=150, disabled=True)
    
    # Reasoning
    st.subheader("💭 Reasoning")
    st.text_area("Comparison Reasoning", log['reasoning'], height=100, disabled=True)


def display_error_details(log: Dict[str, Any]):
    """Display details for error logs."""
    
    st.subheader("❌ Error Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Error Type:** {log['error_type']}")
    
    with col2:
        st.write(f"**Error Message:** {log['error_message']}")
    
    # Context
    st.subheader("🔍 Context")
    st.json(log['context'])


def display_log_analysis():
    """Display log analysis and insights."""
    
    st.subheader("📊 Log Analysis")
    
    logger = ResearchLogger()
    logs = logger.get_logs()
    
    if not logs:
        st.info("No logs available for analysis.")
        return
    
    # Error analysis
    st.subheader("❌ Error Analysis")
    
    error_logs = [log for log in logs if not log.get('success', True)]
    
    if error_logs:
        error_types = {}
        for log in error_logs:
            error_type = log.get('error_type', 'Unknown')
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Error Frequency:**")
            for error_type, count in error_types.items():
                st.write(f"- {error_type}: {count}")
        
        with col2:
            st.write("**Recent Errors:**")
            for log in error_logs[-5:]:
                st.write(f"- {log['timestamp']}: {log.get('error_message', 'Unknown error')}")
    else:
        st.success("No errors found in current logs!")
    
    # Performance analysis
    st.subheader("⚡ Performance Analysis")
    
    api_logs = [log for log in logs if log['type'] == 'api_call' and log.get('response_time')]
    
    if api_logs:
        response_times = [log['response_time'] for log in api_logs]
        avg_response_time = sum(response_times) / len(response_times)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Response Time", f"{avg_response_time:.2f}s")
        
        with col2:
            st.metric("Fastest Response", f"{min(response_times):.2f}s")
        
        with col3:
            st.metric("Slowest Response", f"{max(response_times):.2f}s")
    
    # Prompt test analysis
    st.subheader("🧪 Prompt Test Analysis")
    
    prompt_logs = [log for log in logs if log['type'] == 'prompt_test']
    
    if prompt_logs:
        prompt_types = {}
        for log in prompt_logs:
            prompt_type = log['prompt_type']
            if prompt_type not in prompt_types:
                prompt_types[prompt_type] = {'total': 0, 'success': 0}
            prompt_types[prompt_type]['total'] += 1
            if log.get('success', True):
                prompt_types[prompt_type]['success'] += 1
        
        for prompt_type, stats in prompt_types.items():
            success_rate = (stats['success'] / stats['total']) * 100
            st.write(f"**{prompt_type}:** {success_rate:.1f}% success rate ({stats['success']}/{stats['total']})")


# Global logger instance
research_logger = ResearchLogger()


def get_research_logger() -> ResearchLogger:
    """Get the global research logger instance."""
    return research_logger


if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Research Logger")
    
    tab1, tab2 = st.tabs(["🔍 View Logs", "📊 Log Analysis"])
    
    with tab1:
        display_research_logs()
    
    with tab2:
        display_log_analysis()