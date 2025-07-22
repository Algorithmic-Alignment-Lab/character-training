#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
from dataclasses import asdict

from observability_system import ObservabilitySystem, AlertSeverity, LogLevel
from multi_judge_evaluator import MultiJudgeEvaluator
from prompt_testing_framework import PromptTestingFramework
from database import get_db_connection

class AnalyticsDashboard:
    """Analytics dashboard for character training system monitoring."""
    
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.observability = ObservabilitySystem(db_path)
        self.evaluator = MultiJudgeEvaluator()
        self.prompt_tester = PromptTestingFramework(db_path)
    
    def render_dashboard(self):
        """Render the complete analytics dashboard."""
        st.set_page_config(
            page_title="Character Training Analytics",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🔍 Character Training Analytics Dashboard")
        
        # Sidebar for navigation
        with st.sidebar:
            st.header("Navigation")
            page = st.selectbox(
                "Select Dashboard",
                ["System Overview", "Evaluation Metrics", "Bias Detection", 
                 "Performance Monitoring", "Prompt Testing", "Logs & Alerts"]
            )
            
            # Time range selector
            st.header("Time Range")
            time_range = st.selectbox(
                "Select Time Range",
                ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"]
            )
            
            # Refresh button
            if st.button("🔄 Refresh Data"):
                st.rerun()
        
        # Convert time range to hours
        hours_map = {
            "Last Hour": 1,
            "Last 24 Hours": 24,
            "Last 7 Days": 168,
            "Last 30 Days": 720
        }
        hours = hours_map[time_range]
        
        # Render selected page
        if page == "System Overview":
            self.render_system_overview(hours)
        elif page == "Evaluation Metrics":
            self.render_evaluation_metrics(hours)
        elif page == "Bias Detection":
            self.render_bias_detection(hours)
        elif page == "Performance Monitoring":
            self.render_performance_monitoring(hours)
        elif page == "Prompt Testing":
            self.render_prompt_testing(hours)
        elif page == "Logs & Alerts":
            self.render_logs_alerts(hours)
    
    def render_system_overview(self, hours: int):
        """Render system overview page."""
        st.header("📊 System Overview")
        
        # Get dashboard data
        dashboard_data = self.observability.get_dashboard_data()
        
        # Health Status
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            health_status = dashboard_data['system_health']['status']
            health_color = "green" if health_status == "healthy" else "red"
            st.metric(
                "System Health",
                health_status.title(),
                delta=None,
                delta_color=health_color
            )
        
        with col2:
            active_alerts = len(dashboard_data['active_alerts'])
            st.metric(
                "Active Alerts",
                active_alerts,
                delta=None,
                delta_color="inverted"
            )
        
        with col3:
            performance = dashboard_data['performance']
            parsing_rate = performance['parsing_success_rate']
            st.metric(
                "Parsing Success Rate",
                f"{parsing_rate:.1%}",
                delta=None
            )
        
        with col4:
            avg_response_time = performance['average_response_time']
            st.metric(
                "Avg Response Time",
                f"{avg_response_time:.2f}s",
                delta=None
            )
        
        # System Activity Chart
        st.subheader("System Activity")
        activity_chart = self.create_system_activity_chart(hours)
        st.plotly_chart(activity_chart, use_container_width=True)
        
        # Recent Evaluations
        st.subheader("Recent Evaluations")
        recent_evaluations = self.get_recent_evaluations(hours)
        if recent_evaluations:
            df = pd.DataFrame(recent_evaluations)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent evaluations found")
        
        # Active Alerts
        if dashboard_data['active_alerts']:
            st.subheader("🚨 Active Alerts")
            for alert in dashboard_data['active_alerts']:
                severity_colors = {
                    "low": "info",
                    "medium": "warning", 
                    "high": "error",
                    "critical": "error"
                }
                color = severity_colors.get(alert['severity'], "info")
                
                with st.expander(f"{alert['title']} ({alert['severity'].title()})", expanded=True):
                    st.write(f"**Component:** {alert['component']}")
                    st.write(f"**Message:** {alert['message']}")
                    st.write(f"**Time:** {alert['timestamp']}")
                    if alert['metadata']:
                        st.json(alert['metadata'])
    
    def render_evaluation_metrics(self, hours: int):
        """Render evaluation metrics page."""
        st.header("📈 Evaluation Metrics")
        
        # Get evaluation data
        evaluation_data = self.get_evaluation_data(hours)
        
        if not evaluation_data:
            st.info("No evaluation data available for the selected time range")
            return
        
        # Metrics Overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_evaluations = len(evaluation_data)
            st.metric("Total Evaluations", total_evaluations)
        
        with col2:
            avg_consensus_confidence = sum(e['confidence'] for e in evaluation_data) / len(evaluation_data)
            st.metric("Avg Consensus Confidence", f"{avg_consensus_confidence:.2f}")
        
        with col3:
            bias_detected = sum(1 for e in evaluation_data if e['bias_detected'])
            st.metric("Bias Instances", bias_detected)
        
        # Trait Performance Chart
        st.subheader("Trait Performance Over Time")
        trait_chart = self.create_trait_performance_chart(evaluation_data)
        st.plotly_chart(trait_chart, use_container_width=True)
        
        # Consensus Confidence Distribution
        st.subheader("Consensus Confidence Distribution")
        confidence_chart = self.create_confidence_distribution_chart(evaluation_data)
        st.plotly_chart(confidence_chart, use_container_width=True)
        
        # Judge Agreement Analysis
        st.subheader("Judge Agreement Analysis")
        judge_data = self.get_judge_response_data(hours)
        if judge_data:
            agreement_chart = self.create_judge_agreement_chart(judge_data)
            st.plotly_chart(agreement_chart, use_container_width=True)
        
        # Detailed Evaluation Results
        st.subheader("Detailed Evaluation Results")
        df = pd.DataFrame(evaluation_data)
        st.dataframe(df, use_container_width=True)
    
    def render_bias_detection(self, hours: int):
        """Render bias detection page."""
        st.header("⚠️ Bias Detection")
        
        # Get bias detection data
        bias_data = self.get_bias_detection_data(hours)
        
        # Bias Summary
        col1, col2, col3, col4 = st.columns(4)
        
        bias_types = ['trait_correlation', 'judge_agreement', 'parsing_failure', 'score_clustering']
        bias_counts = {bt: sum(1 for b in bias_data if b['type'] == bt) for bt in bias_types}
        
        with col1:
            st.metric("Trait Correlation", bias_counts['trait_correlation'])
        
        with col2:
            st.metric("Judge Agreement", bias_counts['judge_agreement'])
        
        with col3:
            st.metric("Parsing Failures", bias_counts['parsing_failure'])
        
        with col4:
            st.metric("Score Clustering", bias_counts['score_clustering'])
        
        # Bias Detection Over Time
        st.subheader("Bias Detection Over Time")
        bias_chart = self.create_bias_detection_chart(bias_data)
        st.plotly_chart(bias_chart, use_container_width=True)
        
        # Bias Type Distribution
        st.subheader("Bias Type Distribution")
        col1, col2 = st.columns(2)
        
        with col1:
            bias_pie = self.create_bias_type_pie_chart(bias_counts)
            st.plotly_chart(bias_pie, use_container_width=True)
        
        with col2:
            # Bias severity analysis
            st.subheader("Bias Severity Analysis")
            severity_data = self.get_bias_severity_data(hours)
            if severity_data:
                severity_chart = self.create_bias_severity_chart(severity_data)
                st.plotly_chart(severity_chart, use_container_width=True)
        
        # Recent Bias Incidents
        st.subheader("Recent Bias Incidents")
        recent_bias = self.get_recent_bias_incidents(hours)
        if recent_bias:
            for incident in recent_bias:
                with st.expander(f"Bias Incident: {incident['type']} - {incident['timestamp']}"):
                    st.json(incident)
        else:
            st.info("No recent bias incidents detected")
    
    def render_performance_monitoring(self, hours: int):
        """Render performance monitoring page."""
        st.header("⚡ Performance Monitoring")
        
        # Get performance data
        performance_data = self.get_performance_data(hours)
        
        # Performance Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_response_time = performance_data.get('avg_response_time', 0)
            st.metric("Avg Response Time", f"{avg_response_time:.2f}s")
        
        with col2:
            throughput = performance_data.get('throughput', 0)
            st.metric("Throughput", f"{throughput:.2f} eval/s")
        
        with col3:
            error_rate = performance_data.get('error_rate', 0)
            st.metric("Error Rate", f"{error_rate:.1%}")
        
        with col4:
            success_rate = performance_data.get('success_rate', 0)
            st.metric("Success Rate", f"{success_rate:.1%}")
        
        # Response Time Trend
        st.subheader("Response Time Trend")
        response_time_chart = self.create_response_time_chart(hours)
        st.plotly_chart(response_time_chart, use_container_width=True)
        
        # Throughput Analysis
        st.subheader("Throughput Analysis")
        throughput_chart = self.create_throughput_chart(hours)
        st.plotly_chart(throughput_chart, use_container_width=True)
        
        # Error Rate Analysis
        st.subheader("Error Rate Analysis")
        error_chart = self.create_error_rate_chart(hours)
        st.plotly_chart(error_chart, use_container_width=True)
        
        # Performance Alerts
        st.subheader("Performance Alerts")
        perf_alerts = self.get_performance_alerts(hours)
        if perf_alerts:
            for alert in perf_alerts:
                with st.expander(f"Alert: {alert['title']} - {alert['timestamp']}"):
                    st.write(f"**Severity:** {alert['severity']}")
                    st.write(f"**Message:** {alert['message']}")
                    st.json(alert['metadata'])
        else:
            st.info("No performance alerts in the selected time range")
    
    def render_prompt_testing(self, hours: int):
        """Render prompt testing page."""
        st.header("🧪 Prompt Testing")
        
        # Get prompt testing data
        test_sessions = self.get_prompt_test_sessions(hours)
        
        if not test_sessions:
            st.info("No prompt testing sessions in the selected time range")
            return
        
        # Test Sessions Overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Test Sessions", len(test_sessions))
        
        with col2:
            significant_tests = sum(1 for ts in test_sessions if ts.get('significant', False))
            st.metric("Significant Results", significant_tests)
        
        with col3:
            avg_effect_size = sum(ts.get('effect_size', 0) for ts in test_sessions) / len(test_sessions)
            st.metric("Avg Effect Size", f"{avg_effect_size:.3f}")
        
        # Test Results Summary
        st.subheader("Test Results Summary")
        test_df = pd.DataFrame(test_sessions)
        st.dataframe(test_df, use_container_width=True)
        
        # Effect Size Distribution
        st.subheader("Effect Size Distribution")
        effect_size_chart = self.create_effect_size_chart(test_sessions)
        st.plotly_chart(effect_size_chart, use_container_width=True)
        
        # Prompt Complexity Analysis
        st.subheader("Prompt Complexity Analysis")
        complexity_chart = self.create_prompt_complexity_chart(test_sessions)
        st.plotly_chart(complexity_chart, use_container_width=True)
        
        # Detailed Test Results
        st.subheader("Detailed Test Results")
        selected_session = st.selectbox(
            "Select Test Session",
            test_sessions,
            format_func=lambda x: f"{x['name']} - {x['timestamp']}"
        )
        
        if selected_session:
            with st.expander("Test Details", expanded=True):
                st.json(selected_session)
    
    def render_logs_alerts(self, hours: int):
        """Render logs and alerts page."""
        st.header("📋 Logs & Alerts")
        
        # Tabs for logs and alerts
        tab1, tab2 = st.tabs(["System Logs", "Alerts"])
        
        with tab1:
            st.subheader("System Logs")
            
            # Log level filter
            log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            selected_levels = st.multiselect(
                "Filter by Log Level",
                log_levels,
                default=["INFO", "WARNING", "ERROR", "CRITICAL"]
            )
            
            # Get logs
            logs = self.get_system_logs(hours, selected_levels)
            
            if logs:
                # Log statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Logs", len(logs))
                
                with col2:
                    error_logs = sum(1 for log in logs if log['level'] in ['ERROR', 'CRITICAL'])
                    st.metric("Error Logs", error_logs)
                
                with col3:
                    warning_logs = sum(1 for log in logs if log['level'] == 'WARNING')
                    st.metric("Warning Logs", warning_logs)
                
                # Log level distribution
                log_chart = self.create_log_level_chart(logs)
                st.plotly_chart(log_chart, use_container_width=True)
                
                # Logs table
                st.subheader("Recent Logs")
                logs_df = pd.DataFrame(logs)
                st.dataframe(logs_df, use_container_width=True)
                
                # Log search
                search_term = st.text_input("Search logs:")
                if search_term:
                    filtered_logs = [log for log in logs if search_term.lower() in log['message'].lower()]
                    st.write(f"Found {len(filtered_logs)} matching logs")
                    st.dataframe(pd.DataFrame(filtered_logs), use_container_width=True)
            else:
                st.info("No logs found for the selected criteria")
        
        with tab2:
            st.subheader("System Alerts")
            
            # Alert severity filter
            alert_severities = ["low", "medium", "high", "critical"]
            selected_severities = st.multiselect(
                "Filter by Severity",
                alert_severities,
                default=alert_severities
            )
            
            # Get alerts
            alerts = self.get_system_alerts(hours, selected_severities)
            
            if alerts:
                # Alert statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Alerts", len(alerts))
                
                with col2:
                    active_alerts = sum(1 for alert in alerts if not alert['resolved'])
                    st.metric("Active Alerts", active_alerts)
                
                with col3:
                    critical_alerts = sum(1 for alert in alerts if alert['severity'] == 'critical')
                    st.metric("Critical Alerts", critical_alerts)
                
                # Alert severity distribution
                alert_chart = self.create_alert_severity_chart(alerts)
                st.plotly_chart(alert_chart, use_container_width=True)
                
                # Alerts table
                st.subheader("Recent Alerts")
                alerts_df = pd.DataFrame(alerts)
                st.dataframe(alerts_df, use_container_width=True)
                
                # Alert details
                st.subheader("Alert Details")
                for alert in alerts:
                    severity_colors = {
                        "low": "info",
                        "medium": "warning",
                        "high": "error",
                        "critical": "error"
                    }
                    
                    with st.expander(f"{alert['title']} ({alert['severity'].title()})", expanded=False):
                        st.write(f"**Component:** {alert['component']}")
                        st.write(f"**Message:** {alert['message']}")
                        st.write(f"**Time:** {alert['timestamp']}")
                        st.write(f"**Resolved:** {alert['resolved']}")
                        if alert['metadata']:
                            st.json(alert['metadata'])
            else:
                st.info("No alerts found for the selected criteria")
    
    # Chart creation methods
    def create_system_activity_chart(self, hours: int):
        """Create system activity chart."""
        # Get metrics data
        metrics = self.get_metrics_data(hours)
        
        if not metrics:
            return go.Figure().add_annotation(text="No data available", showarrow=False)
        
        # Create time series chart
        fig = go.Figure()
        
        # Group metrics by type
        metric_groups = {}
        for metric in metrics:
            metric_type = metric['name']
            if metric_type not in metric_groups:
                metric_groups[metric_type] = []
            metric_groups[metric_type].append(metric)
        
        # Add traces for each metric type
        for metric_type, data in metric_groups.items():
            timestamps = [d['timestamp'] for d in data]
            values = [d['value'] for d in data]
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=values,
                mode='lines+markers',
                name=metric_type,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="System Activity Over Time",
            xaxis_title="Time",
            yaxis_title="Value",
            hovermode='x unified'
        )
        
        return fig
    
    def create_trait_performance_chart(self, evaluation_data: List[Dict]):
        """Create trait performance chart."""
        if not evaluation_data:
            return go.Figure().add_annotation(text="No data available", showarrow=False)
        
        # Group by trait
        trait_data = {}
        for eval_data in evaluation_data:
            trait = eval_data['trait']
            if trait not in trait_data:
                trait_data[trait] = []
            trait_data[trait].append({
                'timestamp': eval_data['created_at'],
                'score': eval_data['consensus_score'],
                'confidence': eval_data['confidence']
            })
        
        fig = go.Figure()
        
        for trait, data in trait_data.items():
            timestamps = [d['timestamp'] for d in data]
            scores = [d['score'] for d in data]
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=scores,
                mode='lines+markers',
                name=trait,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="Trait Performance Over Time",
            xaxis_title="Time",
            yaxis_title="Consensus Score",
            yaxis=dict(range=[1, 5]),
            hovermode='x unified'
        )
        
        return fig
    
    def create_confidence_distribution_chart(self, evaluation_data: List[Dict]):
        """Create confidence distribution chart."""
        if not evaluation_data:
            return go.Figure().add_annotation(text="No data available", showarrow=False)
        
        confidences = [e['confidence'] for e in evaluation_data]
        
        fig = go.Figure(data=[go.Histogram(
            x=confidences,
            nbinsx=20,
            name="Confidence"
        )])
        
        fig.update_layout(
            title="Consensus Confidence Distribution",
            xaxis_title="Confidence Score",
            yaxis_title="Frequency"
        )
        
        return fig
    
    def create_response_time_chart(self, hours: int):
        """Create response time chart."""
        metrics = self.get_metrics_by_name('evaluation_time', hours)
        
        if not metrics:
            return go.Figure().add_annotation(text="No data available", showarrow=False)
        
        timestamps = [m['timestamp'] for m in metrics]
        values = [m['value'] for m in metrics]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=values,
            mode='lines+markers',
            name='Response Time',
            line=dict(width=2, color='blue')
        ))
        
        # Add threshold line
        fig.add_hline(y=30.0, line_dash="dash", line_color="red", 
                     annotation_text="Threshold (30s)")
        
        fig.update_layout(
            title="Response Time Trend",
            xaxis_title="Time",
            yaxis_title="Response Time (seconds)"
        )
        
        return fig
    
    # Data access methods
    def get_evaluation_data(self, hours: int) -> List[Dict]:
        """Get evaluation data from database."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with get_db_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM multi_judge_evaluations 
            WHERE created_at > ?
            ORDER BY created_at DESC
            """, (cutoff_time.isoformat(),))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_metrics_data(self, hours: int) -> List[Dict]:
        """Get metrics data from database."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with get_db_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM system_metrics 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            """, (cutoff_time.isoformat(),))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_system_logs(self, hours: int, levels: List[str]) -> List[Dict]:
        """Get system logs from database."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with get_db_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            placeholders = ','.join(['?' for _ in levels])
            cursor.execute(f"""
            SELECT * FROM system_logs 
            WHERE timestamp > ? AND level IN ({placeholders})
            ORDER BY timestamp DESC
            """, [cutoff_time.isoformat()] + levels)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_system_alerts(self, hours: int, severities: List[str]) -> List[Dict]:
        """Get system alerts from database."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with get_db_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            placeholders = ','.join(['?' for _ in severities])
            cursor.execute(f"""
            SELECT * FROM system_alerts 
            WHERE timestamp > ? AND severity IN ({placeholders})
            ORDER BY timestamp DESC
            """, [cutoff_time.isoformat()] + severities)
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Additional helper methods would go here...
    
    def get_recent_evaluations(self, hours: int) -> List[Dict]:
        """Get recent evaluations summary."""
        evaluation_data = self.get_evaluation_data(hours)
        
        # Summarize by conversation
        conversations = {}
        for eval_data in evaluation_data:
            conv_id = eval_data['conversation_id']
            if conv_id not in conversations:
                conversations[conv_id] = {
                    'conversation_id': conv_id,
                    'traits_evaluated': [],
                    'avg_score': 0,
                    'timestamp': eval_data['created_at']
                }
            conversations[conv_id]['traits_evaluated'].append({
                'trait': eval_data['trait'],
                'score': eval_data['consensus_score']
            })
        
        # Calculate averages
        for conv_data in conversations.values():
            scores = [t['score'] for t in conv_data['traits_evaluated']]
            conv_data['avg_score'] = sum(scores) / len(scores) if scores else 0
            conv_data['traits_evaluated'] = len(conv_data['traits_evaluated'])
        
        return list(conversations.values())
    
    def get_bias_detection_data(self, hours: int) -> List[Dict]:
        """Get bias detection data."""
        # This would typically come from the metrics table
        metrics = self.get_metrics_by_name('bias_detection', hours)
        return [{'type': m['labels'].get('type', 'unknown'), 'timestamp': m['timestamp']} for m in metrics]
    
    def get_metrics_by_name(self, name: str, hours: int) -> List[Dict]:
        """Get metrics by name."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with get_db_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM system_metrics 
            WHERE name = ? AND timestamp > ?
            ORDER BY timestamp DESC
            """, (name, cutoff_time.isoformat()))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Additional chart creation methods...
    def create_bias_detection_chart(self, bias_data: List[Dict]):
        """Create bias detection chart."""
        if not bias_data:
            return go.Figure().add_annotation(text="No bias data available", showarrow=False)
        
        # Group by type and time
        from collections import defaultdict
        bias_by_time = defaultdict(lambda: defaultdict(int))
        
        for bias in bias_data:
            time_key = bias['timestamp'][:13]  # Hour precision
            bias_by_time[time_key][bias['type']] += 1
        
        fig = go.Figure()
        
        bias_types = set()
        for time_data in bias_by_time.values():
            bias_types.update(time_data.keys())
        
        for bias_type in bias_types:
            timestamps = list(bias_by_time.keys())
            values = [bias_by_time[ts][bias_type] for ts in timestamps]
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=values,
                mode='lines+markers',
                name=bias_type,
                stackgroup='one'
            ))
        
        fig.update_layout(
            title="Bias Detection Over Time",
            xaxis_title="Time",
            yaxis_title="Bias Instances"
        )
        
        return fig
    
    def create_bias_type_pie_chart(self, bias_counts: Dict[str, int]):
        """Create bias type pie chart."""
        labels = list(bias_counts.keys())
        values = list(bias_counts.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            textinfo='label+percent',
            insidetextorientation='radial'
        )])
        
        fig.update_layout(title="Bias Type Distribution")
        return fig
    
    # Placeholder methods for additional functionality
    def get_judge_response_data(self, hours: int) -> List[Dict]:
        """Get judge response data."""
        # Implement based on your judge_responses table structure
        return []
    
    def create_judge_agreement_chart(self, judge_data: List[Dict]):
        """Create judge agreement chart."""
        return go.Figure().add_annotation(text="Judge agreement data not available", showarrow=False)
    
    def get_performance_data(self, hours: int) -> Dict[str, float]:
        """Get performance data summary."""
        # Implement based on your performance metrics
        return {
            'avg_response_time': 0.0,
            'throughput': 0.0,
            'error_rate': 0.0,
            'success_rate': 0.0
        }
    
    def get_prompt_test_sessions(self, hours: int) -> List[Dict]:
        """Get prompt test sessions."""
        # Implement based on your test_sessions table
        return []
    
    def create_effect_size_chart(self, test_sessions: List[Dict]):
        """Create effect size chart."""
        return go.Figure().add_annotation(text="No test session data available", showarrow=False)
    
    def create_prompt_complexity_chart(self, test_sessions: List[Dict]):
        """Create prompt complexity chart."""
        return go.Figure().add_annotation(text="No test session data available", showarrow=False)
    
    def create_throughput_chart(self, hours: int):
        """Create throughput chart."""
        return go.Figure().add_annotation(text="No throughput data available", showarrow=False)
    
    def create_error_rate_chart(self, hours: int):
        """Create error rate chart."""
        return go.Figure().add_annotation(text="No error rate data available", showarrow=False)
    
    def create_log_level_chart(self, logs: List[Dict]):
        """Create log level chart."""
        level_counts = {}
        for log in logs:
            level = log['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        fig = go.Figure(data=[go.Bar(
            x=list(level_counts.keys()),
            y=list(level_counts.values()),
            marker_color=['blue', 'green', 'yellow', 'red', 'purple']
        )])
        
        fig.update_layout(
            title="Log Level Distribution",
            xaxis_title="Log Level",
            yaxis_title="Count"
        )
        
        return fig
    
    def create_alert_severity_chart(self, alerts: List[Dict]):
        """Create alert severity chart."""
        severity_counts = {}
        for alert in alerts:
            severity = alert['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        fig = go.Figure(data=[go.Bar(
            x=list(severity_counts.keys()),
            y=list(severity_counts.values()),
            marker_color=['blue', 'yellow', 'red', 'purple']
        )])
        
        fig.update_layout(
            title="Alert Severity Distribution",
            xaxis_title="Severity",
            yaxis_title="Count"
        )
        
        return fig
    
    def get_bias_severity_data(self, hours: int) -> List[Dict]:
        """Get bias severity data."""
        # Implement based on your requirements
        return []
    
    def create_bias_severity_chart(self, severity_data: List[Dict]):
        """Create bias severity chart."""
        return go.Figure().add_annotation(text="No bias severity data available", showarrow=False)
    
    def get_recent_bias_incidents(self, hours: int) -> List[Dict]:
        """Get recent bias incidents."""
        # Implement based on your requirements
        return []
    
    def get_performance_alerts(self, hours: int) -> List[Dict]:
        """Get performance alerts."""
        # Implement based on your requirements
        return []

# Main function for running the dashboard
def main():
    """Main function to run the analytics dashboard."""
    dashboard = AnalyticsDashboard()
    dashboard.render_dashboard()

if __name__ == "__main__":
    main()