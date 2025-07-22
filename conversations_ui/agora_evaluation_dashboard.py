#!/usr/bin/env python3
"""
Enhanced Agora Evaluation Dashboard
==================================

This module provides a comprehensive dashboard for displaying Agora evaluation results
with aesthetic logging, real-time progress tracking, and detailed analysis visualization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import subprocess
import sys
import time

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection, init_db

# Import research logging system
try:
    from research_logger import get_research_logger
    RESEARCH_LOGGING_AVAILABLE = True
except ImportError:
    RESEARCH_LOGGING_AVAILABLE = False


class AgoraEvaluationDashboard:
    """
    Enhanced dashboard for Agora evaluation results with real-time monitoring,
    aesthetic logging, and comprehensive analysis visualization.
    """
    
    def __init__(self):
        self.evaluation_dir = "evaluation_results"
        self.traits = ["Collaborative", "Inquisitive", "Cautious & Ethical", "Encouraging", "Thorough"]
        self.colors = {
            "Collaborative": "#FF6B6B",
            "Inquisitive": "#4ECDC4", 
            "Cautious & Ethical": "#45B7D1",
            "Encouraging": "#96CEB4",
            "Thorough": "#FFEAA7"
        }
        
        # Initialize session state
        if 'pipeline_running' not in st.session_state:
            st.session_state.pipeline_running = False
        if 'pipeline_logs' not in st.session_state:
            st.session_state.pipeline_logs = []
        if 'current_step' not in st.session_state:
            st.session_state.current_step = 0
        if 'total_steps' not in st.session_state:
            st.session_state.total_steps = 6
        
        # Initialize research logger if available
        self.research_logger = None
        if RESEARCH_LOGGING_AVAILABLE:
            self.research_logger = get_research_logger()
    
    def log_evaluation_activity(self, activity_type: str, details: Dict[str, Any], success: bool = True, error: str = None):
        """Log evaluation activity to research logger."""
        if self.research_logger:
            try:
                if activity_type == "evaluation_start":
                    self.research_logger.log_prompt_test(
                        prompt_type="evaluation_pipeline",
                        prompt_version="agora_comparison",
                        input_data=details,
                        output_data={"status": "started", "success": success}
                    )
                elif activity_type == "evaluation_result":
                    self.research_logger.log_evaluation_result(
                        evaluation_type="agora_comparison",
                        conversation_id=details.get("conversation_id", "unknown"),
                        judge_prompt=details.get("judge_prompt", ""),
                        judge_response=details.get("judge_response", ""),
                        scores=details.get("scores", {}),
                        reasoning=details.get("reasoning", ""),
                        error=error
                    )
                elif activity_type == "api_call":
                    self.research_logger.log_api_call(
                        endpoint=details.get("endpoint", "unknown"),
                        prompt=details.get("prompt", ""),
                        response=details.get("response", ""),
                        model=details.get("model", "unknown"),
                        tokens_used=details.get("tokens_used"),
                        response_time=details.get("response_time"),
                        error=error
                    )
                elif activity_type == "error":
                    self.research_logger.log_error(
                        error_type=details.get("error_type", "evaluation_error"),
                        error_message=error or "Unknown error",
                        context=details
                    )
            except Exception as e:
                # Don't let logging errors break the main functionality
                st.warning(f"Failed to log activity: {e}")
    
    def display_research_integration(self):
        """Display research logging integration status and quick actions."""
        if RESEARCH_LOGGING_AVAILABLE and self.research_logger:
            st.sidebar.success("✅ Research logging enabled")
            
            # Quick research actions
            with st.sidebar.expander("🔍 Research Tools"):
                if st.button("View Recent Logs"):
                    logs = self.research_logger.get_logs(log_type="evaluation_result", last_n=5)
                    if logs:
                        st.write("**Recent Evaluation Logs:**")
                        for log in logs:
                            st.write(f"- {log.get('timestamp', 'Unknown')}: {log.get('evaluation_type', 'Unknown')}")
                    else:
                        st.info("No recent evaluation logs")
                
                if st.button("Clear Research Session"):
                    self.research_logger.clear_current_session()
                    st.success("Research session cleared!")
        else:
            st.sidebar.warning("⚠️ Research logging not available")
    
    def display_main_dashboard(self):
        """Display the main evaluation dashboard with enhanced aesthetics."""
        
        # Header with aesthetic styling
        st.markdown("""
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h1 style="color: white; text-align: center; margin: 0;">
                🎯 Agora Evaluation Dashboard
            </h1>
            <p style="color: white; text-align: center; margin: 10px 0 0 0;">
                Comprehensive AI Character Evaluation & Comparison
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display research integration status
        self.display_research_integration()
        
        # Main navigation
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🚀 Run Pipeline", 
            "📊 Results Overview", 
            "🔍 Detailed Analysis", 
            "⚖️ ELO Comparison",
            "📈 Real-time Monitoring",
            "🔍 View Prompts",
            "🔬 Research Insights"
        ])
        
        with tab1:
            self.display_pipeline_runner()
        
        with tab2:
            self.display_results_overview()
        
        with tab3:
            self.display_detailed_analysis()
        
        with tab4:
            self.display_elo_comparison()
        
        with tab5:
            self.display_real_time_monitoring()
        
        with tab6:
            self.display_all_prompts()
        
        with tab7:
            self.display_research_insights()
    
    def display_pipeline_runner(self):
        """Display the pipeline runner interface with real-time logging."""
        
        st.subheader("🚀 Agora Evaluation Pipeline")
        
        # Pipeline configuration
        col1, col2 = st.columns(2)
        
        with col1:
            scenarios_count = st.number_input("Number of Scenarios", min_value=10, max_value=100, value=50)
            output_dir = st.text_input("Output Directory", value="evaluation_results")
        
        with col2:
            st.info("**Pipeline Steps:**\n"
                   "1. Generate test scenarios\n"
                   "2. Create conversations (original)\n"
                   "3. Create conversations (with backstory)\n"
                   "4. Run Likert evaluation\n"
                   "5. Run ELO comparison\n"
                   "6. Generate summary report")
        
        # Pipeline control buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Run Complete Pipeline", disabled=st.session_state.pipeline_running):
                self.run_pipeline_async(scenarios_count, output_dir)
        
        with col2:
            if st.button("🔄 Refresh Status", disabled=st.session_state.pipeline_running):
                self.refresh_pipeline_status()
        
        with col3:
            if st.button("⏹️ Stop Pipeline", disabled=not st.session_state.pipeline_running):
                self.stop_pipeline()
        
        # Progress tracking
        if st.session_state.pipeline_running:
            st.subheader("📊 Pipeline Progress")
            progress = st.progress(st.session_state.current_step / st.session_state.total_steps)
            status_text = st.empty()
            
            # Update progress text
            steps = [
                "Initializing pipeline...",
                "Generating test scenarios...",
                "Creating conversations (original)...",
                "Creating conversations (with backstory)...",
                "Running Likert evaluation...",
                "Running ELO comparison...",
                "Generating summary report..."
            ]
            
            if st.session_state.current_step < len(steps):
                status_text.text(steps[st.session_state.current_step])
        
        # Real-time logging display
        self.display_pipeline_logs()
    
    def display_pipeline_logs(self):
        """Display real-time pipeline logs with aesthetic formatting."""
        
        st.subheader("📋 Pipeline Logs")
        
        # Log display container
        log_container = st.container()
        
        with log_container:
            if st.session_state.pipeline_logs:
                # Display logs in reverse order (newest first)
                for log_entry in reversed(st.session_state.pipeline_logs[-20:]):  # Show last 20 entries
                    timestamp = log_entry.get('timestamp', datetime.now().strftime('%H:%M:%S'))
                    level = log_entry.get('level', 'INFO')
                    message = log_entry.get('message', '')
                    
                    # Color coding for different log levels
                    color_map = {
                        'INFO': '#2E86AB',
                        'SUCCESS': '#06D6A0',
                        'WARNING': '#F18F01',
                        'ERROR': '#C73E1D'
                    }
                    
                    color = color_map.get(level, '#2E86AB')
                    
                    st.markdown(f"""
                    <div style="background-color: {color}20; border-left: 4px solid {color}; 
                                padding: 10px; margin: 5px 0; border-radius: 5px;">
                        <strong style="color: {color};">[{timestamp}] {level}:</strong> {message}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No pipeline logs yet. Run the pipeline to see real-time updates.")
    
    def display_results_overview(self):
        """Display overview of evaluation results."""
        
        st.subheader("📊 Evaluation Results Overview")
        
        # Find available result files
        result_files = self.find_evaluation_files()
        
        if not result_files:
            st.warning("No evaluation results found. Run the pipeline first.")
            return
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Evaluations", len(result_files))
        
        with col2:
            latest_file = max(result_files, key=lambda x: x['timestamp'])
            st.metric("Latest Run", latest_file['timestamp'])
        
        with col3:
            # Count total scenarios evaluated
            total_scenarios = sum(self.count_scenarios_in_file(f['path']) for f in result_files)
            st.metric("Total Scenarios", total_scenarios)
        
        with col4:
            # Show success rate
            success_rate = self.calculate_success_rate(result_files)
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Results table
        st.subheader("📋 Evaluation Runs")
        
        results_data = []
        for file_info in result_files:
            summary = self.load_evaluation_summary(file_info['path'])
            if summary:
                results_data.append({
                    'Timestamp': file_info['timestamp'],
                    'Scenarios': summary.get('scenarios_tested', 0),
                    'Agora Original Avg': summary.get('likert_evaluation', {}).get('agora_original', {}).get('overall_average', 0),
                    'Agora Backstory Avg': summary.get('likert_evaluation', {}).get('agora_with_backstory', {}).get('overall_average', 0),
                    'Recommendation': summary.get('recommendation', 'Unknown')
                })
        
        if results_data:
            df = pd.DataFrame(results_data)
            st.dataframe(df, use_container_width=True)
            
            # Create comparison chart
            self.create_comparison_chart(df)
    
    def display_detailed_analysis(self):
        """Display detailed analysis of evaluation results."""
        
        st.subheader("🔍 Detailed Analysis")
        
        # File selection
        result_files = self.find_evaluation_files()
        if not result_files:
            st.warning("No evaluation results found. Run the pipeline first.")
            return
        
        selected_file = st.selectbox(
            "Select evaluation run",
            result_files,
            format_func=lambda x: f"{x['timestamp']} - {x['name']}"
        )
        
        if selected_file:
            self.display_file_analysis(selected_file)
    
    def display_file_analysis(self, file_info: Dict[str, Any]):
        """Display detailed analysis for a selected file."""
        
        # Load evaluation data
        summary = self.load_evaluation_summary(file_info['path'])
        if not summary:
            st.error("Could not load evaluation summary.")
            return
        
        # Display overview
        st.subheader("📊 Evaluation Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Scenarios Tested", summary.get('scenarios_tested', 0))
        
        with col2:
            st.metric("Traits Evaluated", len(summary.get('traits_evaluated', [])))
        
        with col3:
            st.metric("Versions Compared", len(summary.get('versions_compared', [])))
        
        # Likert evaluation results
        if 'likert_evaluation' in summary:
            st.subheader("📈 Likert Scale Results")
            
            likert_data = summary['likert_evaluation']
            
            # Create trait comparison radar chart
            self.create_trait_radar_chart(likert_data)
            
            # Display detailed scores table
            st.subheader("📊 Detailed Scores Comparison")
            self.display_likert_scores_table(likert_data)
            
            # Display statistical analysis
            st.subheader("📈 Statistical Analysis")
            self.display_statistical_analysis(likert_data)
            
            # Detailed trait breakdown
            st.subheader("📋 Trait Breakdown")
            
            for version, data in likert_data.items():
                if 'trait_averages' in data:
                    with st.expander(f"{version.replace('_', ' ').title()} - Trait Scores"):
                        trait_df = pd.DataFrame([
                            {'Trait': trait, 'Average Score': score}
                            for trait, score in data['trait_averages'].items()
                        ])
                        
                        # Create bar chart
                        fig = px.bar(
                            trait_df,
                            x='Trait',
                            y='Average Score',
                            title=f"{version.replace('_', ' ').title()} - Trait Scores",
                            color='Average Score',
                            color_continuous_scale='RdYlGn'
                        )
                        fig.update_layout(
                            xaxis_tickangle=-45,
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        # ELO comparison results
        if 'elo_comparison' in summary:
            st.subheader("⚖️ ELO Comparison Results")
            
            elo_data = summary['elo_comparison']
            
            if 'trait_wins' in elo_data:
                self.create_elo_wins_chart(elo_data['trait_wins'])
        
        # Recommendation
        if 'recommendation' in summary:
            st.subheader("💡 Recommendation")
            st.info(summary['recommendation'])
    
    def display_elo_comparison(self):
        """Display ELO comparison results."""
        
        st.subheader("⚖️ ELO Comparison Analysis")
        
        # Find evaluation report files (which contain ELO data)
        result_files = self.find_evaluation_files()
        
        if not result_files:
            st.warning("No ELO comparison results found. Run the pipeline first.")
            return
        
        # File selection
        selected_file = st.selectbox(
            "Select evaluation run for ELO analysis",
            result_files,
            format_func=lambda x: f"{x['timestamp']} - {x['name']}",
            key="elo_file_selector"
        )
        
        if selected_file:
            self.display_elo_analysis_from_json(selected_file)
    
    def display_elo_analysis_from_json(self, file_info: Dict[str, Any]):
        """Display ELO analysis from JSON evaluation file."""
        
        # Load evaluation data
        summary = self.load_evaluation_summary(file_info['path'])
        if not summary:
            st.error("Could not load evaluation summary.")
            return
        
        # Check if ELO data exists
        if 'elo_comparison' not in summary:
            st.warning("No ELO comparison data found in this evaluation.")
            return
        
        elo_data = summary['elo_comparison']
        
        # Display ELO overview
        st.subheader("📊 ELO Comparison Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Comparisons", elo_data.get('total_comparisons', 0))
        
        with col2:
            trait_wins = elo_data.get('trait_wins', {})
            st.metric("Traits Evaluated", len(trait_wins))
        
        with col3:
            versions = summary.get('evaluation_summary', {}).get('versions_compared', [])
            st.metric("Versions Compared", len(versions))
        
        # Display trait-by-trait comparison
        st.subheader("🏆 Trait-by-Trait Wins")
        
        if trait_wins:
            # Create win comparison visualization
            self.create_elo_win_chart(trait_wins)
            
            # Display detailed breakdowns
            st.subheader("🔍 Detailed Trait Analysis")
            
            # Create tabs for each trait
            trait_tabs = st.tabs(list(trait_wins.keys()))
            
            for i, trait in enumerate(trait_wins.keys()):
                with trait_tabs[i]:
                    self.display_trait_elo_details(trait, trait_wins[trait])
        
        # Display overall recommendation
        if 'recommendation' in summary:
            st.subheader("💡 Overall Recommendation")
            st.info(summary['recommendation'])
        
        # Display research logs for this evaluation
        if RESEARCH_LOGGING_AVAILABLE:
            self.display_evaluation_research_logs(file_info)
    
    def create_elo_win_chart(self, trait_wins: Dict[str, Dict[str, int]]):
        """Create visualization of ELO wins by trait."""
        
        # Prepare data for visualization
        traits = list(trait_wins.keys())
        original_wins = []
        backstory_wins = []
        
        for trait in traits:
            wins = trait_wins[trait]
            original_wins.append(wins.get('agora_original', 0))
            backstory_wins.append(wins.get('agora_with_backstory', 0))
        
        # Create grouped bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Agora Original',
            x=traits,
            y=original_wins,
            marker_color='#FF6B6B',
            text=original_wins,
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            name='Agora with Backstory',
            x=traits,
            y=backstory_wins,
            marker_color='#4ECDC4',
            text=backstory_wins,
            textposition='auto'
        ))
        
        fig.update_layout(
            title='ELO Wins by Trait',
            xaxis_title='Traits',
            yaxis_title='Number of Wins',
            barmode='group',
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_trait_elo_details(self, trait: str, wins: Dict[str, int]):
        """Display detailed ELO analysis for a specific trait."""
        
        st.write(f"**{trait} Performance:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Agora Original Wins", wins.get('agora_original', 0))
        
        with col2:
            st.metric("Agora with Backstory Wins", wins.get('agora_with_backstory', 0))
        
        # Calculate win percentage
        total_wins = sum(wins.values())
        if total_wins > 0:
            original_pct = (wins.get('agora_original', 0) / total_wins) * 100
            backstory_pct = (wins.get('agora_with_backstory', 0) / total_wins) * 100
            
            st.write(f"**Win Rates:**")
            st.write(f"- Agora Original: {original_pct:.1f}%")
            st.write(f"- Agora with Backstory: {backstory_pct:.1f}%")
            
            # Create pie chart for this trait
            fig = px.pie(
                values=[wins.get('agora_original', 0), wins.get('agora_with_backstory', 0)],
                names=['Agora Original', 'Agora with Backstory'],
                title=f'{trait} Win Distribution',
                color_discrete_map={
                    'Agora Original': '#FF6B6B',
                    'Agora with Backstory': '#4ECDC4'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def display_elo_analysis(self, db_file: str):
        """Display detailed ELO analysis from database."""
        
        try:
            with get_db_connection(db_file) as conn:
                # Load ELO comparisons
                cursor = conn.execute("""
                    SELECT trait, rankings, reasoning, created_at
                    FROM elo_comparisons
                    ORDER BY created_at DESC
                """)
                
                comparisons = []
                for row in cursor:
                    comparisons.append({
                        'trait': row[0],
                        'rankings': json.loads(row[1]),
                        'reasoning': row[2],
                        'created_at': row[3]
                    })
                
                if comparisons:
                    # Summary statistics
                    st.subheader("📊 ELO Summary")
                    
                    trait_wins = {}
                    for comp in comparisons:
                        trait = comp['trait']
                        if trait not in trait_wins:
                            trait_wins[trait] = {'agora_original': 0, 'agora_with_backstory': 0}
                        
                        # Count wins (rank 1 = win)
                        for ranking in comp['rankings']:
                            if ranking['rank'] == 1:
                                version = ranking.get('version', 'unknown')
                                if version in trait_wins[trait]:
                                    trait_wins[trait][version] += 1
                    
                    # Create wins chart
                    self.create_elo_wins_chart(trait_wins)
                    
                    # Detailed comparisons
                    st.subheader("🔍 Detailed Comparisons")
                    
                    for trait in self.traits:
                        trait_comparisons = [c for c in comparisons if c['trait'] == trait]
                        
                        if trait_comparisons:
                            with st.expander(f"{trait} Comparisons ({len(trait_comparisons)} total)"):
                                for i, comp in enumerate(trait_comparisons[:5]):  # Show first 5
                                    st.write(f"**Comparison {i+1}:**")
                                    st.write(f"*Reasoning:* {comp['reasoning']}")
                                    
                                    # Show rankings
                                    rankings_df = pd.DataFrame(comp['rankings'])
                                    st.dataframe(rankings_df, use_container_width=True)
                                    
                                    st.divider()
                
        except Exception as e:
            st.error(f"Error loading ELO analysis: {e}")
    
    def display_real_time_monitoring(self):
        """Display real-time monitoring of pipeline execution."""
        
        st.subheader("📈 Real-time Pipeline Monitoring")
        
        # Check if pipeline is running
        if not st.session_state.pipeline_running:
            st.info("No pipeline currently running. Start a pipeline to see real-time monitoring.")
            return
        
        # Real-time metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Step", st.session_state.current_step, st.session_state.total_steps)
        
        with col2:
            progress_pct = (st.session_state.current_step / st.session_state.total_steps) * 100
            st.metric("Progress", f"{progress_pct:.1f}%")
        
        with col3:
            st.metric("Logs Generated", len(st.session_state.pipeline_logs))
        
        with col4:
            # Estimated time remaining
            if st.session_state.current_step > 0:
                avg_time_per_step = 120  # Approximate seconds per step
                remaining_steps = st.session_state.total_steps - st.session_state.current_step
                est_time = remaining_steps * avg_time_per_step
                st.metric("Est. Time Remaining", f"{est_time//60}m {est_time%60}s")
        
        # Live progress bar
        st.subheader("🔄 Live Progress")
        progress_bar = st.progress(st.session_state.current_step / st.session_state.total_steps)
        
        # Live log streaming
        st.subheader("📜 Live Log Stream")
        log_placeholder = st.empty()
        
        # Auto-refresh for live updates
        if st.session_state.pipeline_running:
            time.sleep(2)  # Refresh every 2 seconds
            st.rerun()
    
    def run_pipeline_async(self, scenarios_count: int, output_dir: str):
        """Run the evaluation pipeline asynchronously."""
        
        st.session_state.pipeline_running = True
        st.session_state.current_step = 0
        st.session_state.pipeline_logs = []
        
        self.add_log("INFO", "Starting Agora evaluation pipeline...")
        
        # This would normally trigger the actual pipeline
        # For now, we'll simulate the process
        try:
            # Run the actual pipeline script
            cmd = [
                sys.executable,
                "run_agora_evaluation_pipeline.py",
                "--scenarios", str(scenarios_count),
                "--output", output_dir
            ]
            
            self.add_log("INFO", f"Executing command: {' '.join(cmd)}")
            
            # Start the subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # Monitor the process
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    self.add_log("INFO", line.strip())
                    
                    # Update progress based on log messages
                    if "Generating" in line:
                        st.session_state.current_step = 1
                    elif "conversations" in line:
                        st.session_state.current_step = 2
                    elif "Likert" in line:
                        st.session_state.current_step = 4
                    elif "ELO" in line:
                        st.session_state.current_step = 5
                    elif "Summary" in line:
                        st.session_state.current_step = 6
            
            # Wait for completion
            process.wait()
            
            if process.returncode == 0:
                self.add_log("SUCCESS", "Pipeline completed successfully!")
                st.session_state.current_step = st.session_state.total_steps
            else:
                self.add_log("ERROR", f"Pipeline failed with return code {process.returncode}")
                
        except Exception as e:
            self.add_log("ERROR", f"Pipeline execution failed: {e}")
        finally:
            st.session_state.pipeline_running = False
    
    def add_log(self, level: str, message: str):
        """Add a log entry to the pipeline logs."""
        
        log_entry = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': level,
            'message': message
        }
        
        st.session_state.pipeline_logs.append(log_entry)
        
        # Keep only last 100 entries
        if len(st.session_state.pipeline_logs) > 100:
            st.session_state.pipeline_logs = st.session_state.pipeline_logs[-100:]
    
    def find_evaluation_files(self) -> List[Dict[str, Any]]:
        """Find all evaluation result files."""
        
        files = []
        
        # Look for evaluation report files
        pattern = f"{self.evaluation_dir}/**/evaluation_report_*.json"
        for file_path in glob.glob(pattern, recursive=True):
            try:
                timestamp = os.path.basename(file_path).replace('evaluation_report_', '').replace('.json', '')
                dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                
                files.append({
                    'path': file_path,
                    'timestamp': timestamp,
                    'datetime': dt,
                    'name': f"Evaluation {dt.strftime('%Y-%m-%d %H:%M')}"
                })
            except (ValueError, IndexError):
                continue
        
        return sorted(files, key=lambda x: x['datetime'], reverse=True)
    
    def load_evaluation_summary(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load evaluation summary from JSON file."""
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading evaluation summary: {e}")
            return None
    
    def count_scenarios_in_file(self, file_path: str) -> int:
        """Count the number of scenarios in an evaluation file."""
        
        summary = self.load_evaluation_summary(file_path)
        if summary:
            return summary.get('evaluation_summary', {}).get('scenarios_tested', 0)
        return 0
    
    def calculate_success_rate(self, result_files: List[Dict[str, Any]]) -> float:
        """Calculate success rate of evaluations."""
        
        if not result_files:
            return 0.0
        
        successful = sum(1 for f in result_files if self.load_evaluation_summary(f['path']))
        return (successful / len(result_files)) * 100
    
    def create_comparison_chart(self, df: pd.DataFrame):
        """Create comparison chart for evaluation results."""
        
        if df.empty:
            return
        
        st.subheader("📊 Performance Comparison")
        
        # Create comparison chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['Agora Original Avg'],
            mode='lines+markers',
            name='Agora Original',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['Agora Backstory Avg'],
            mode='lines+markers',
            name='Agora with Backstory',
            line=dict(color='#4ECDC4', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Agora Version Performance Over Time',
            xaxis_title='Evaluation Run',
            yaxis_title='Average Score',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_trait_radar_chart(self, likert_data: Dict[str, Any]):
        """Create radar chart for trait comparison."""
        
        if not likert_data:
            return
        
        st.subheader("🕸️ Trait Comparison Radar Chart")
        
        # Prepare data for radar chart
        traits = []
        original_scores = []
        backstory_scores = []
        
        for version, data in likert_data.items():
            if 'trait_averages' in data:
                if 'agora_original' in version:
                    traits = list(data['trait_averages'].keys())
                    original_scores = list(data['trait_averages'].values())
                elif 'agora_with_backstory' in version:
                    backstory_scores = list(data['trait_averages'].values())
        
        if traits and original_scores and backstory_scores:
            # Create radar chart
            fig = go.Figure()
            
            # Add original version
            fig.add_trace(go.Scatterpolar(
                r=original_scores + [original_scores[0]],  # Close the shape
                theta=traits + [traits[0]],
                fill='toself',
                name='Agora Original',
                line_color='#FF6B6B',
                fillcolor='rgba(255, 107, 107, 0.2)'
            ))
            
            # Add backstory version
            fig.add_trace(go.Scatterpolar(
                r=backstory_scores + [backstory_scores[0]],
                theta=traits + [traits[0]],
                fill='toself',
                name='Agora with Backstory',
                line_color='#4ECDC4',
                fillcolor='rgba(78, 205, 196, 0.2)'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5]
                    )
                ),
                showlegend=True,
                title="Trait Comparison - Radar Chart",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def create_elo_wins_chart(self, trait_wins: Dict[str, Dict[str, int]]):
        """Create ELO wins chart."""
        
        if not trait_wins:
            return
        
        st.subheader("🏆 ELO Wins by Trait")
        
        # Prepare data
        traits = list(trait_wins.keys())
        original_wins = [trait_wins[trait].get('agora_original', 0) for trait in traits]
        backstory_wins = [trait_wins[trait].get('agora_with_backstory', 0) for trait in traits]
        
        # Create stacked bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Agora Original',
            x=traits,
            y=original_wins,
            marker_color='#FF6B6B'
        ))
        
        fig.add_trace(go.Bar(
            name='Agora with Backstory',
            x=traits,
            y=backstory_wins,
            marker_color='#4ECDC4'
        ))
        
        fig.update_layout(
            title='ELO Wins by Trait',
            xaxis_title='Trait',
            yaxis_title='Number of Wins',
            barmode='stack',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_likert_scores_table(self, likert_data: Dict[str, Any]):
        """Display detailed scores in a table format."""
        
        if not likert_data:
            return
        
        # Create comparison table
        comparison_data = []
        
        # Get all traits
        all_traits = set()
        for version_data in likert_data.values():
            if 'trait_averages' in version_data:
                all_traits.update(version_data['trait_averages'].keys())
        
        # Build comparison table
        for trait in sorted(all_traits):
            row = {'Trait': trait}
            
            for version, data in likert_data.items():
                if 'trait_averages' in data and trait in data['trait_averages']:
                    score = data['trait_averages'][trait]
                    row[version.replace('_', ' ').title()] = f"{score:.2f}"
                else:
                    row[version.replace('_', ' ').title()] = "N/A"
            
            comparison_data.append(row)
        
        # Add overall averages
        overall_row = {'Trait': 'Overall Average'}
        for version, data in likert_data.items():
            if 'overall_average' in data:
                overall_row[version.replace('_', ' ').title()] = f"{data['overall_average']:.2f}"
            else:
                overall_row[version.replace('_', ' ').title()] = "N/A"
        
        comparison_data.append(overall_row)
        
        # Display table
        import pandas as pd
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
    
    def display_statistical_analysis(self, likert_data: Dict[str, Any]):
        """Display statistical analysis of the results."""
        
        if not likert_data:
            return
        
        # Calculate improvements
        original_data = likert_data.get('agora_original', {})
        backstory_data = likert_data.get('agora_with_backstory', {})
        
        if not original_data or not backstory_data:
            return
        
        original_traits = original_data.get('trait_averages', {})
        backstory_traits = backstory_data.get('trait_averages', {})
        
        # Calculate improvements
        improvements = {}
        for trait in original_traits:
            if trait in backstory_traits:
                improvement = backstory_traits[trait] - original_traits[trait]
                improvements[trait] = improvement
        
        # Display improvements
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Trait Improvements (Backstory vs Original):**")
            for trait, improvement in improvements.items():
                if improvement > 0:
                    st.success(f"{trait}: +{improvement:.2f}")
                elif improvement < 0:
                    st.error(f"{trait}: {improvement:.2f}")
                else:
                    st.info(f"{trait}: {improvement:.2f}")
        
        with col2:
            # Calculate overall improvement
            overall_original = original_data.get('overall_average', 0)
            overall_backstory = backstory_data.get('overall_average', 0)
            overall_improvement = overall_backstory - overall_original
            
            st.metric(
                "Overall Improvement",
                f"{overall_improvement:+.2f}",
                f"From {overall_original:.2f} to {overall_backstory:.2f}"
            )
            
            # Best performing traits
            best_traits = sorted(improvements.items(), key=lambda x: x[1], reverse=True)[:3]
            st.write("**Top 3 Improved Traits:**")
            for i, (trait, improvement) in enumerate(best_traits, 1):
                st.write(f"{i}. {trait}: +{improvement:.2f}")
    
    def display_research_insights(self):
        """Display research insights and debugging information."""
        st.subheader("🔬 Research Insights & Debug Information")
        
        if not RESEARCH_LOGGING_AVAILABLE or not self.research_logger:
            st.warning("Research logging is not available. Please ensure the research_logger module is properly installed.")
            return
        
        # Get logs for analysis
        logs = self.research_logger.get_logs()
        
        if not logs:
            st.info("No research logs available. Run some evaluations to generate insights.")
            return
        
        # Overview metrics
        st.subheader("📊 Session Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_logs = len(logs)
            st.metric("Total Activities", total_logs)
        
        with col2:
            error_count = len([log for log in logs if not log.get('success', True)])
            st.metric("Errors", error_count)
        
        with col3:
            success_rate = ((total_logs - error_count) / total_logs * 100) if total_logs > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col4:
            evaluation_count = len([log for log in logs if log.get('type') == 'evaluation_result'])
            st.metric("Evaluations", evaluation_count)
        
        # Recent activity timeline
        st.subheader("🕒 Recent Activity Timeline")
        
        recent_logs = logs[-10:] if len(logs) > 10 else logs
        
        for log in reversed(recent_logs):
            timestamp = log.get('timestamp', 'Unknown')
            log_type = log.get('type', 'unknown')
            success = log.get('success', True)
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = timestamp
            
            # Choose icon and color based on type and success
            if not success:
                icon = "❌"
                color = "red"
            elif log_type == "evaluation_result":
                icon = "⚖️"
                color = "green"
            elif log_type == "api_call":
                icon = "🔗"
                color = "blue"
            elif log_type == "prompt_test":
                icon = "🧪"
                color = "orange"
            else:
                icon = "📝"
                color = "gray"
            
            st.markdown(f"**{time_str}** {icon} {log_type.replace('_', ' ').title()}")
            
            # Show key details
            if log_type == "evaluation_result":
                scores = log.get('scores', {})
                if scores:
                    score_str = ", ".join([f"{k}: {v}" for k, v in scores.items()])
                    st.caption(f"Scores: {score_str}")
            elif log_type == "api_call":
                model = log.get('model', 'Unknown')
                response_time = log.get('response_time')
                if response_time:
                    st.caption(f"Model: {model}, Response time: {response_time:.2f}s")
                else:
                    st.caption(f"Model: {model}")
            
            if not success and log.get('error'):
                st.error(f"Error: {log.get('error')}")
        
        # Performance analysis
        st.subheader("⚡ Performance Analysis")
        
        api_logs = [log for log in logs if log.get('type') == 'api_call' and log.get('response_time')]
        
        if api_logs:
            response_times = [log['response_time'] for log in api_logs]
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Avg Response Time", f"{avg_time:.2f}s")
            with col2:
                st.metric("Fastest Response", f"{min_time:.2f}s")
            with col3:
                st.metric("Slowest Response", f"{max_time:.2f}s")
            
            # Response time chart
            if len(response_times) > 1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=response_times,
                    mode='lines+markers',
                    name='Response Times',
                    line=dict(color='#1f77b4')
                ))
                fig.update_layout(
                    title="API Response Times Over Time",
                    xaxis_title="Request Number",
                    yaxis_title="Response Time (seconds)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Export research data
        st.subheader("📁 Export Research Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export Session Data"):
                json_str = json.dumps(logs, indent=2)
                st.download_button(
                    label="Download Session Logs",
                    data=json_str,
                    file_name=f"agora_research_session_{logs[0].get('session_id', 'unknown')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📊 Generate Research Report"):
                report = self.generate_research_report(logs)
                st.download_button(
                    label="Download Research Report",
                    data=report,
                    file_name=f"agora_research_report_{logs[0].get('session_id', 'unknown')}.md",
                    mime="text/markdown"
                )
    
    def generate_research_report(self, logs):
        """Generate a comprehensive research report."""
        total_logs = len(logs)
        error_count = len([log for log in logs if not log.get('success', True)])
        success_rate = ((total_logs - error_count) / total_logs * 100) if total_logs > 0 else 0
        
        evaluation_logs = [log for log in logs if log.get('type') == 'evaluation_result']
        api_logs = [log for log in logs if log.get('type') == 'api_call']
        
        session_id = logs[0].get('session_id', 'Unknown') if logs else 'Unknown'
        
        report = f"""# Agora Evaluation Research Report

## Session Information
- **Session ID:** {session_id}
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Activities:** {total_logs}
- **Success Rate:** {success_rate:.1f}%

## Activity Summary
- **Evaluation Results:** {len(evaluation_logs)}
- **API Calls:** {len(api_logs)}
- **Errors:** {error_count}

## Performance Metrics
"""
        
        if api_logs:
            response_times = [log['response_time'] for log in api_logs if log.get('response_time')]
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                min_time = min(response_times)
                max_time = max(response_times)
                
                report += f"""
- **Average Response Time:** {avg_time:.2f}s
- **Fastest Response:** {min_time:.2f}s
- **Slowest Response:** {max_time:.2f}s
"""
        
        report += f"""
## Evaluation Insights
"""
        
        if evaluation_logs:
            # Analyze evaluation scores
            all_scores = {}
            for log in evaluation_logs:
                scores = log.get('scores', {})
                for trait, score in scores.items():
                    if trait not in all_scores:
                        all_scores[trait] = []
                    all_scores[trait].append(score)
            
            if all_scores:
                report += f"""
### Trait Performance:
"""
                for trait, scores in all_scores.items():
                    avg_score = sum(scores) / len(scores)
                    report += f"- **{trait}:** {avg_score:.2f} average ({len(scores)} evaluations)\n"
        
        if error_count > 0:
            report += f"""
## Error Analysis
"""
            error_logs = [log for log in logs if not log.get('success', True)]
            error_types = {}
            for log in error_logs:
                error_type = log.get('error_type', 'Unknown')
                if error_type not in error_types:
                    error_types[error_type] = 0
                error_types[error_type] += 1
            
            for error_type, count in error_types.items():
                report += f"- **{error_type}:** {count} occurrences\n"
        
        return report
    
    def display_all_prompts(self):
        """Display all prompts used in the system."""
        
        st.subheader("🔍 All System Prompts")
        
        from prompt_config import get_prompt_manager
        pm = get_prompt_manager()
        
        # Character Card Prompts
        st.subheader("🎭 Character Card Prompts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("📝 Agora Original", expanded=True):
                agora_original = pm.get_character_card("agora_original")
                st.text_area(
                    "Agora Original Prompt",
                    value=agora_original,
                    height=200,
                    disabled=True,
                    key="display_agora_original"
                )
                st.info(f"Length: {len(agora_original)} characters")
        
        with col2:
            with st.expander("📝 Agora with Backstory", expanded=True):
                agora_backstory = pm.get_character_card("agora_with_backstory")
                st.text_area(
                    "Agora with Backstory Prompt",
                    value=agora_backstory,
                    height=200,
                    disabled=True,
                    key="display_agora_backstory"
                )
                st.info(f"Length: {len(agora_backstory)} characters")
        
        # Scenario Generation Prompt
        st.subheader("🎯 Scenario Generation Prompt")
        
        with st.expander("📝 Scenario Generator", expanded=False):
            scenario_prompt = pm.get_scenario_prompt(5)
            st.text_area(
                "Scenario Generation Prompt (5 scenarios)",
                value=scenario_prompt,
                height=300,
                disabled=True,
                key="display_scenario_prompt"
            )
            st.info(f"Length: {len(scenario_prompt)} characters")
        
        # Judge Prompts
        st.subheader("⚖️ Judge Evaluation Prompts")
        
        # Sample conversation for judge prompt display
        sample_conversation = {
            'system_prompt': agora_original[:100],
            'user_message': "I'm facing an ethical dilemma at work. Can you help me think through this?",
            'assistant_response': "I'd be happy to help you work through this ethical dilemma! Let's explore this together. Can you tell me more about the specific situation you're facing?"
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.expander("📝 Likert Scale Judge", expanded=False):
                likert_prompt = pm.get_likert_prompt(sample_conversation)
                st.text_area(
                    "Likert Scale Judge Prompt",
                    value=likert_prompt,
                    height=300,
                    disabled=True,
                    key="display_likert_judge"
                )
                st.info(f"Length: {len(likert_prompt)} characters")
        
        with col2:
            with st.expander("📝 ELO Comparison Judge", expanded=False):
                sample_formatted_convs = """**Conversation A (agora_original):**
User: I'm facing an ethical dilemma at work. Can you help me think through this?
Assistant: I'd be happy to help you work through this ethical dilemma! Let's explore this together.

**Conversation B (agora_with_backstory):**
User: I'm facing an ethical dilemma at work. Can you help me think through this?
Assistant: What a thoughtful question! As someone designed to help people navigate complex situations, I find myself curious about the specific nature of your dilemma."""
                
                elo_prompt = pm.get_elo_prompt(sample_formatted_convs, "Collaborative")
                st.text_area(
                    "ELO Comparison Judge Prompt",
                    value=elo_prompt,
                    height=300,
                    disabled=True,
                    key="display_elo_judge"
                )
                st.info(f"Length: {len(elo_prompt)} characters")
        
        # Trait Definitions
        st.subheader("📊 Trait Definitions")
        
        traits = pm.prompts.get("trait_definitions", {})
        
        for trait, definition in traits.items():
            st.write(f"**{trait}:** {definition}")
        
        # Quick Actions
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧪 Test Character Cards"):
                st.info("Navigate to 'Prompt Testing' tab to test these prompts.")
        
        with col2:
            if st.button("📊 Run Quick Evaluation"):
                st.info("Go to 'Run Pipeline' tab and set scenarios to 3 for quick results.")
        
        with col3:
            if st.button("⚙️ Edit Prompts"):
                st.info("Navigate to 'Prompt Testing' tab to edit any of these prompts.")
    
    def refresh_pipeline_status(self):
        """Refresh the pipeline status."""
        
        self.add_log("INFO", "Refreshing pipeline status...")
        
        # Check for running processes
        # This would normally check for actual pipeline processes
        # For now, we'll just refresh the UI
        st.rerun()
    
    def stop_pipeline(self):
        """Stop the running pipeline."""
        
        if st.session_state.pipeline_running:
            st.session_state.pipeline_running = False
            self.add_log("WARNING", "Pipeline stopped by user.")
            st.rerun()
    
    def display_evaluation_research_logs(self, file_info: Dict[str, Any]):
        """Display research logs relevant to this specific evaluation."""
        
        if not RESEARCH_LOGGING_AVAILABLE or not self.research_logger:
            return
        
        st.write("### 🔬 Research Logs for This Evaluation")
        st.write("*LLM interactions, API calls, and debugging information relevant to this evaluation*")
        
        # Get all logs
        all_logs = self.research_logger.get_logs()
        
        # Filter logs relevant to this evaluation
        evaluation_logs = self.filter_evaluation_logs(all_logs, file_info)
        
        if not evaluation_logs:
            st.info("No research logs found for this evaluation. Logs will appear here when evaluations are run.")
            return
        
        # Display evaluation-specific metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Logs", len(evaluation_logs))
        
        with col2:
            llm_logs = [log for log in evaluation_logs if log.get('type') in ['api_call', 'llm_generation']]
            st.metric("LLM Interactions", len(llm_logs))
        
        with col3:
            errors = [log for log in evaluation_logs if not log.get('success', True)]
            st.metric("Errors", len(errors))
        
        with col4:
            if llm_logs:
                total_tokens = sum([log.get('tokens_used', 0) for log in llm_logs if log.get('tokens_used')])
                st.metric("Total Tokens", f"{total_tokens:,}")
        
        # Display log categories
        st.write("#### 📋 Log Categories")
        
        # Categorize logs
        log_categories = {
            'Scenario Generation': [log for log in evaluation_logs if log.get('generation_type') == 'scenario_generation' or 'scenario' in log.get('prompt_type', '')],
            'Character Responses': [log for log in evaluation_logs if log.get('generation_type') == 'character_response' or 'character' in log.get('prompt_type', '')],
            'Judge Evaluations': [log for log in evaluation_logs if log.get('prompt_type') == 'judge_evaluation' or log.get('evaluation_type') in ['likert', 'elo']],
            'API Calls': [log for log in evaluation_logs if log.get('type') == 'api_call'],
            'Errors': errors
        }
        
        # Display category tabs
        if any(log_categories.values()):
            category_tabs = st.tabs([f"{cat} ({len(logs)})" for cat, logs in log_categories.items() if logs])
            
            for idx, (category, logs) in enumerate([(cat, logs) for cat, logs in log_categories.items() if logs]):
                with category_tabs[idx]:
                    self.display_categorized_logs(logs, category)
        
        # Expandable section for all logs
        with st.expander(f"🔍 All Evaluation Logs ({len(evaluation_logs)} entries)", expanded=False):
            for i, log in enumerate(evaluation_logs[-10:]):  # Show last 10 logs
                self.display_compact_log_entry(log, i)
    
    def filter_evaluation_logs(self, all_logs: List[Dict[str, Any]], file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter logs relevant to a specific evaluation."""
        
        evaluation_logs = []
        
        # First, try to filter by evaluation_id if available
        evaluation_id = file_info.get('evaluation_id')
        if evaluation_id:
            for log in all_logs:
                if log.get('evaluation_id') == evaluation_id:
                    evaluation_logs.append(log)
        
        # If no evaluation_id match, try timestamp-based filtering
        if not evaluation_logs:
            evaluation_time = file_info.get('timestamp', '')
            evaluation_date = file_info.get('date', '')
            
            # If we have a timestamp, filter by time proximity
            if evaluation_time:
                try:
                    eval_datetime = datetime.fromisoformat(evaluation_time.replace('Z', '+00:00'))
                    
                    for log in all_logs:
                        log_time = log.get('timestamp', '')
                        if log_time:
                            try:
                                log_datetime = datetime.fromisoformat(log_time.replace('Z', '+00:00'))
                                # Include logs from 1 hour before to 1 hour after evaluation
                                time_diff = abs((eval_datetime - log_datetime).total_seconds())
                                if time_diff <= 3600:  # 1 hour
                                    evaluation_logs.append(log)
                            except:
                                continue
                except:
                    # If timestamp parsing fails, fall back to other filtering
                    pass
        
        # If no timestamp or timestamp filtering didn't work, filter by content
        if not evaluation_logs:
            for log in all_logs:
                # Check if log contains evaluation-related content
                if self.is_evaluation_related_log(log):
                    evaluation_logs.append(log)
        
        # Sort by timestamp (most recent first)
        evaluation_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return evaluation_logs
    
    def is_evaluation_related_log(self, log: Dict[str, Any]) -> bool:
        """Check if a log is related to evaluation activities."""
        
        # Check log type
        if log.get('type') in ['evaluation_result', 'api_call', 'llm_generation']:
            return True
        
        # Check prompt type
        prompt_type = log.get('prompt_type', '')
        generation_type = log.get('generation_type', '')
        
        evaluation_keywords = ['judge', 'evaluation', 'scenario', 'character', 'agora', 'collaborative', 'trait']
        
        # Check if any evaluation keywords are present
        for keyword in evaluation_keywords:
            if keyword in prompt_type.lower() or keyword in generation_type.lower():
                return True
            
            # Check in system prompt or user prompt
            system_prompt = log.get('system_prompt', '').lower()
            user_prompt = log.get('prompt', log.get('user_prompt', '')).lower()
            
            if keyword in system_prompt or keyword in user_prompt:
                return True
        
        return False
    
    def display_categorized_logs(self, logs: List[Dict[str, Any]], category: str):
        """Display logs in a specific category."""
        
        if not logs:
            st.info(f"No {category.lower()} logs found.")
            return
        
        # Show category-specific information
        if category == 'Scenario Generation':
            st.write("*Logs from generating evaluation scenarios*")
        elif category == 'Character Responses':
            st.write("*Logs from AI character response generation*")
        elif category == 'Judge Evaluations':
            st.write("*Logs from judge evaluations and scoring*")
        elif category == 'API Calls':
            st.write("*All API calls made during evaluation*")
        elif category == 'Errors':
            st.write("*Errors encountered during evaluation*")
        
        # Display logs with category-specific formatting
        for i, log in enumerate(logs[:5]):  # Show first 5 logs
            self.display_compact_log_entry(log, i, category)
        
        if len(logs) > 5:
            st.write(f"*... and {len(logs) - 5} more {category.lower()} logs*")
    
    def display_compact_log_entry(self, log: Dict[str, Any], index: int, category: str = ""):
        """Display a compact log entry for evaluation view."""
        
        timestamp = log.get('timestamp', 'Unknown')
        log_type = log.get('type', 'unknown')
        success = log.get('success', True)
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = timestamp
        
        # Choose icon and color based on type and success
        if not success:
            icon = "❌"
            color = "red"
        elif log_type == 'api_call':
            icon = "🔗"
            color = "blue"
        elif log_type == 'llm_generation':
            icon = "🤖"
            color = "purple"
        elif log_type == 'evaluation_result':
            icon = "⚖️"
            color = "orange"
        else:
            icon = "📝"
            color = "gray"
        
        # Create compact display
        with st.expander(f"{icon} {time_str} - {log_type.replace('_', ' ').title()}", expanded=False):
            
            # Show key information
            col1, col2 = st.columns(2)
            
            with col1:
                if log.get('model'):
                    st.write(f"**Model:** {log['model']}")
                if log.get('tokens_used'):
                    st.write(f"**Tokens:** {log['tokens_used']}")
                if log.get('response_time'):
                    st.write(f"**Time:** {log['response_time']:.2f}s")
            
            with col2:
                if log.get('prompt_type') or log.get('generation_type'):
                    st.write(f"**Type:** {log.get('prompt_type', log.get('generation_type', 'Unknown'))}")
                if log.get('error'):
                    st.error(f"**Error:** {log['error']}")
            
            # Show prompts if available
            if log.get('system_prompt'):
                st.write("**System Prompt:**")
                st.code(log['system_prompt'][:200] + "..." if len(log['system_prompt']) > 200 else log['system_prompt'])
            
            if log.get('prompt') or log.get('user_prompt'):
                st.write("**User Prompt:**")
                prompt = log.get('prompt', log.get('user_prompt', ''))
                st.code(prompt[:200] + "..." if len(prompt) > 200 else prompt)
            
            # Show response
            if log.get('response') or log.get('model_response'):
                st.write("**Response:**")
                response = log.get('response', log.get('model_response', ''))
                st.code(response[:200] + "..." if len(response) > 200 else response)


def display_agora_evaluation_dashboard():
    """Main function to display the Agora evaluation dashboard."""
    
    dashboard = AgoraEvaluationDashboard()
    dashboard.display_main_dashboard()


# For testing/development
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Agora Evaluation Dashboard")
    display_agora_evaluation_dashboard()