#!/usr/bin/env python3

import json
import time
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, deque
import statistics

from database import get_db_connection, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: LogLevel
    component: str
    message: str
    metadata: Dict[str, Any]
    trace_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class Metric:
    """Metric data point."""
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    metadata: Dict[str, Any]

@dataclass
class Alert:
    """Alert notification."""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    component: str
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics for evaluation system."""
    parsing_success_rate: float
    average_response_time: float
    consensus_confidence: float
    judge_agreement: float
    trait_independence: float
    error_rate: float
    throughput: float
    bias_detection_rate: float

class StructuredLogger:
    """Structured logging system with contextual information."""
    
    def __init__(self, component: str, db_path: str = "conversations.db"):
        self.component = component
        self.db_path = db_path
        self.trace_id = None
        self.session_id = None
        self._init_logging_tables()
    
    def _init_logging_tables(self):
        """Initialize logging tables."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT NOT NULL,
                trace_id TEXT,
                session_id TEXT
            )
            """)
            
            conn.commit()
    
    def set_context(self, trace_id: str = None, session_id: str = None):
        """Set logging context."""
        self.trace_id = trace_id
        self.session_id = session_id
    
    def log(self, level: LogLevel, message: str, metadata: Dict[str, Any] = None, 
            trace_id: str = None, session_id: str = None):
        """Log a structured message."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            component=self.component,
            message=message,
            metadata=metadata or {},
            trace_id=trace_id or self.trace_id,
            session_id=session_id or self.session_id
        )
        
        # Log to database
        self._save_log_entry(entry)
        
        # Log to console
        console_message = f"[{entry.timestamp.isoformat()}] {entry.level.value} - {entry.component}: {entry.message}"
        if entry.metadata:
            console_message += f" | {json.dumps(entry.metadata)}"
        
        if entry.level == LogLevel.DEBUG:
            logger.debug(console_message)
        elif entry.level == LogLevel.INFO:
            logger.info(console_message)
        elif entry.level == LogLevel.WARNING:
            logger.warning(console_message)
        elif entry.level == LogLevel.ERROR:
            logger.error(console_message)
        elif entry.level == LogLevel.CRITICAL:
            logger.critical(console_message)
    
    def debug(self, message: str, metadata: Dict[str, Any] = None):
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, metadata)
    
    def info(self, message: str, metadata: Dict[str, Any] = None):
        """Log info message."""
        self.log(LogLevel.INFO, message, metadata)
    
    def warning(self, message: str, metadata: Dict[str, Any] = None):
        """Log warning message."""
        self.log(LogLevel.WARNING, message, metadata)
    
    def error(self, message: str, metadata: Dict[str, Any] = None):
        """Log error message."""
        self.log(LogLevel.ERROR, message, metadata)
    
    def critical(self, message: str, metadata: Dict[str, Any] = None):
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, metadata)
    
    def _save_log_entry(self, entry: LogEntry):
        """Save log entry to database."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO system_logs 
                (id, timestamp, level, component, message, metadata, trace_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    entry.timestamp.isoformat(),
                    entry.level.value,
                    entry.component,
                    entry.message,
                    json.dumps(entry.metadata),
                    entry.trace_id,
                    entry.session_id
                ))
                conn.commit()
        except Exception as e:
            # Fallback to console logging if database fails
            logger.error(f"Failed to save log entry to database: {e}")

class MetricsCollector:
    """Collects and stores system metrics."""
    
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.metrics_buffer = deque(maxlen=1000)  # In-memory buffer
        self._init_metrics_tables()
    
    def _init_metrics_tables(self):
        """Initialize metrics tables."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TEXT NOT NULL,
                labels TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
            """)
            
            conn.commit()
    
    def record_metric(self, name: str, metric_type: MetricType, value: float, 
                     labels: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Record a metric value."""
        metric = Metric(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            metadata=metadata or {}
        )
        
        # Add to buffer
        self.metrics_buffer.append(metric)
        
        # Save to database
        self._save_metric(metric)
    
    def record_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Record a counter metric."""
        self.record_metric(name, MetricType.COUNTER, value, labels)
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric."""
        self.record_metric(name, MetricType.GAUGE, value, labels)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric."""
        self.record_metric(name, MetricType.HISTOGRAM, value, labels)
    
    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None):
        """Record a timer metric."""
        self.record_metric(name, MetricType.TIMER, duration, labels)
    
    def _save_metric(self, metric: Metric):
        """Save metric to database."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO system_metrics 
                (id, name, metric_type, value, timestamp, labels, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    metric.name,
                    metric.metric_type.value,
                    metric.value,
                    metric.timestamp.isoformat(),
                    json.dumps(metric.labels),
                    json.dumps(metric.metadata)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save metric to database: {e}")
    
    def get_recent_metrics(self, metric_name: str, minutes: int = 60) -> List[Metric]:
        """Get recent metrics for a given name."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with get_db_connection(self.db_path) as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM system_metrics 
            WHERE name = ? AND timestamp > ?
            ORDER BY timestamp DESC
            """, (metric_name, cutoff_time.isoformat()))
            
            rows = cursor.fetchall()
            
            metrics = []
            for row in rows:
                metrics.append(Metric(
                    name=row['name'],
                    metric_type=MetricType(row['metric_type']),
                    value=row['value'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    labels=json.loads(row['labels']),
                    metadata=json.loads(row['metadata'])
                ))
            
            return metrics

class AlertSystem:
    """Alert system for monitoring and notifications."""
    
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.alert_handlers = []
        self.active_alerts = {}
        self._init_alert_tables()
    
    def _init_alert_tables(self):
        """Initialize alert tables."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_alerts (
                id TEXT PRIMARY KEY,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                component TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT NOT NULL,
                resolved BOOLEAN NOT NULL DEFAULT FALSE,
                resolved_at TEXT
            )
            """)
            
            conn.commit()
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler."""
        self.alert_handlers.append(handler)
    
    def send_alert(self, severity: AlertSeverity, title: str, message: str, 
                   component: str, metadata: Dict[str, Any] = None):
        """Send an alert."""
        alert = Alert(
            id=str(uuid.uuid4()),
            severity=severity,
            title=title,
            message=message,
            component=component,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Save to database
        self._save_alert(alert)
        
        # Store in active alerts
        self.active_alerts[alert.id] = alert
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
        
        return alert.id
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            # Update database
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                UPDATE system_alerts 
                SET resolved = TRUE, resolved_at = ?
                WHERE id = ?
                """, (alert.resolved_at.isoformat(), alert_id))
                conn.commit()
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
    
    def _save_alert(self, alert: Alert):
        """Save alert to database."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO system_alerts 
                (id, severity, title, message, component, timestamp, metadata, resolved, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id,
                    alert.severity.value,
                    alert.title,
                    alert.message,
                    alert.component,
                    alert.timestamp.isoformat(),
                    json.dumps(alert.metadata),
                    alert.resolved,
                    alert.resolved_at.isoformat() if alert.resolved_at else None
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save alert to database: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())

class BiasMonitor:
    """Monitors for bias patterns in evaluation results."""
    
    def __init__(self, alert_system: AlertSystem, metrics_collector: MetricsCollector):
        self.alert_system = alert_system
        self.metrics_collector = metrics_collector
        self.bias_thresholds = {
            'trait_correlation': 0.95,
            'judge_agreement': 0.05,  # Too low agreement
            'parsing_failure_rate': 0.20,  # Too high failure rate
            'score_clustering': 0.80  # Too much clustering
        }
    
    def monitor_evaluation_results(self, evaluation_results: Dict[str, Any]):
        """Monitor evaluation results for bias patterns."""
        self._check_trait_correlation(evaluation_results)
        self._check_judge_agreement(evaluation_results)
        self._check_parsing_success(evaluation_results)
        self._check_score_distribution(evaluation_results)
    
    def _check_trait_correlation(self, results: Dict[str, Any]):
        """Check for excessive trait correlation."""
        trait_results = results.get('trait_results', [])
        if len(trait_results) < 2:
            return
        
        # Calculate correlation between traits
        trait_scores = {}
        for trait_result in trait_results:
            trait = trait_result['trait']
            score = trait_result['consensus_score']
            trait_scores[trait] = score
        
        # If all traits have the same score, it's suspicious
        scores = list(trait_scores.values())
        if len(set(scores)) == 1:
            self.alert_system.send_alert(
                AlertSeverity.HIGH,
                "Trait Correlation Bias Detected",
                f"All traits received identical scores: {scores[0]}",
                "BiasMonitor",
                {'trait_scores': trait_scores}
            )
            
            self.metrics_collector.record_counter("bias_detection", 1.0, {'type': 'trait_correlation'})
    
    def _check_judge_agreement(self, results: Dict[str, Any]):
        """Check for abnormal judge agreement patterns."""
        metrics = results.get('metrics')
        if not metrics:
            return
        
        if hasattr(metrics, 'judge_agreement') and metrics.judge_agreement < self.bias_thresholds['judge_agreement']:
            self.alert_system.send_alert(
                AlertSeverity.MEDIUM,
                "Low Judge Agreement Detected",
                f"Judge agreement rate: {metrics.judge_agreement:.2%}",
                "BiasMonitor",
                {'judge_agreement': metrics.judge_agreement}
            )
            
            self.metrics_collector.record_counter("bias_detection", 1.0, {'type': 'judge_agreement'})
    
    def _check_parsing_success(self, results: Dict[str, Any]):
        """Check for high parsing failure rates."""
        metrics = results.get('metrics')
        if not metrics:
            return
        
        if hasattr(metrics, 'parsing_success_rate') and metrics.parsing_success_rate < (1 - self.bias_thresholds['parsing_failure_rate']):
            self.alert_system.send_alert(
                AlertSeverity.HIGH,
                "High Parsing Failure Rate Detected",
                f"Parsing success rate: {metrics.parsing_success_rate:.2%}",
                "BiasMonitor",
                {'parsing_success_rate': metrics.parsing_success_rate}
            )
            
            self.metrics_collector.record_counter("bias_detection", 1.0, {'type': 'parsing_failure'})
    
    def _check_score_distribution(self, results: Dict[str, Any]):
        """Check for abnormal score clustering."""
        trait_results = results.get('trait_results', [])
        if not trait_results:
            return
        
        scores = [tr['consensus_score'] for tr in trait_results]
        if not scores:
            return
        
        # Check for excessive clustering
        score_counts = {}
        for score in scores:
            rounded_score = round(score, 1)
            score_counts[rounded_score] = score_counts.get(rounded_score, 0) + 1
        
        max_count = max(score_counts.values())
        clustering_ratio = max_count / len(scores)
        
        if clustering_ratio > self.bias_thresholds['score_clustering']:
            self.alert_system.send_alert(
                AlertSeverity.MEDIUM,
                "Score Clustering Detected",
                f"Score clustering ratio: {clustering_ratio:.2%}",
                "BiasMonitor",
                {'score_distribution': score_counts}
            )
            
            self.metrics_collector.record_counter("bias_detection", 1.0, {'type': 'score_clustering'})

class PerformanceMonitor:
    """Monitors system performance metrics."""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_system: AlertSystem):
        self.metrics_collector = metrics_collector
        self.alert_system = alert_system
        self.performance_thresholds = {
            'response_time': 30.0,  # seconds
            'error_rate': 0.10,  # 10%
            'throughput': 1.0,  # evaluations per second
            'memory_usage': 0.80  # 80% of available memory
        }
    
    def monitor_evaluation_performance(self, evaluation_results: Dict[str, Any]):
        """Monitor evaluation performance."""
        metrics = evaluation_results.get('metrics')
        if not metrics:
            return
        
        # Record performance metrics
        if hasattr(metrics, 'evaluation_time'):
            self.metrics_collector.record_timer('evaluation_time', metrics.evaluation_time)
            
            if metrics.evaluation_time > self.performance_thresholds['response_time']:
                self.alert_system.send_alert(
                    AlertSeverity.MEDIUM,
                    "Slow Evaluation Performance",
                    f"Evaluation took {metrics.evaluation_time:.2f} seconds",
                    "PerformanceMonitor",
                    {'evaluation_time': metrics.evaluation_time}
                )
        
        if hasattr(metrics, 'parsing_success_rate'):
            error_rate = 1 - metrics.parsing_success_rate
            self.metrics_collector.record_gauge('error_rate', error_rate)
            
            if error_rate > self.performance_thresholds['error_rate']:
                self.alert_system.send_alert(
                    AlertSeverity.HIGH,
                    "High Error Rate Detected",
                    f"Error rate: {error_rate:.2%}",
                    "PerformanceMonitor",
                    {'error_rate': error_rate}
                )
        
        if hasattr(metrics, 'total_evaluations'):
            self.metrics_collector.record_counter('total_evaluations', metrics.total_evaluations)
    
    def get_performance_summary(self, hours: int = 24) -> PerformanceMetrics:
        """Get performance summary for the last N hours."""
        # Get recent metrics
        response_times = self.metrics_collector.get_recent_metrics('evaluation_time', hours * 60)
        error_rates = self.metrics_collector.get_recent_metrics('error_rate', hours * 60)
        evaluations = self.metrics_collector.get_recent_metrics('total_evaluations', hours * 60)
        
        # Calculate averages
        avg_response_time = statistics.mean([m.value for m in response_times]) if response_times else 0.0
        avg_error_rate = statistics.mean([m.value for m in error_rates]) if error_rates else 0.0
        total_evaluations = sum([m.value for m in evaluations])
        
        # Calculate throughput
        throughput = total_evaluations / (hours * 3600) if hours > 0 else 0.0
        
        return PerformanceMetrics(
            parsing_success_rate=1 - avg_error_rate,
            average_response_time=avg_response_time,
            consensus_confidence=0.0,  # Would need to track this separately
            judge_agreement=0.0,  # Would need to track this separately
            trait_independence=0.0,  # Would need to track this separately
            error_rate=avg_error_rate,
            throughput=throughput,
            bias_detection_rate=0.0  # Would need to track this separately
        )

class ObservabilitySystem:
    """Comprehensive observability system for character training."""
    
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.logger = StructuredLogger("ObservabilitySystem", db_path)
        self.metrics_collector = MetricsCollector(db_path)
        self.alert_system = AlertSystem(db_path)
        self.bias_monitor = BiasMonitor(self.alert_system, self.metrics_collector)
        self.performance_monitor = PerformanceMonitor(self.metrics_collector, self.alert_system)
        
        # Set up default alert handlers
        self.alert_system.add_alert_handler(self._console_alert_handler)
        
        self.logger.info("Observability system initialized")
    
    def _console_alert_handler(self, alert: Alert):
        """Default console alert handler."""
        severity_emoji = {
            AlertSeverity.LOW: "ℹ️",
            AlertSeverity.MEDIUM: "⚠️",
            AlertSeverity.HIGH: "🚨",
            AlertSeverity.CRITICAL: "💥"
        }
        
        emoji = severity_emoji.get(alert.severity, "❓")
        print(f"{emoji} ALERT [{alert.severity.value.upper()}] {alert.title}")
        print(f"   Component: {alert.component}")
        print(f"   Message: {alert.message}")
        print(f"   Time: {alert.timestamp.isoformat()}")
        if alert.metadata:
            print(f"   Metadata: {json.dumps(alert.metadata, indent=2)}")
        print()
    
    def monitor_evaluation(self, evaluation_results: Dict[str, Any]):
        """Monitor evaluation results for issues."""
        conversation_id = evaluation_results.get('conversation_id')
        
        # Set logging context
        trace_id = str(uuid.uuid4())
        self.logger.set_context(trace_id=trace_id, session_id=conversation_id)
        
        # Log evaluation
        self.logger.info(
            "Evaluation completed",
            {
                'conversation_id': conversation_id,
                'traits_evaluated': len(evaluation_results.get('trait_results', [])),
                'bias_warnings': len(evaluation_results.get('bias_warnings', [])),
                'metrics': asdict(evaluation_results.get('metrics')) if evaluation_results.get('metrics') else None
            }
        )
        
        # Monitor for bias
        self.bias_monitor.monitor_evaluation_results(evaluation_results)
        
        # Monitor performance
        self.performance_monitor.monitor_evaluation_performance(evaluation_results)
        
        # Log any bias warnings
        for warning in evaluation_results.get('bias_warnings', []):
            self.logger.warning(f"Bias warning: {warning}", {'conversation_id': conversation_id})
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for monitoring UI."""
        # Get recent performance metrics
        performance = self.performance_monitor.get_performance_summary(24)
        
        # Get active alerts
        active_alerts = self.alert_system.get_active_alerts()
        
        # Get recent logs
        with get_db_connection(self.db_path) as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            cursor = conn.cursor()
            
            # Recent logs
            cursor.execute("""
            SELECT * FROM system_logs 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC 
            LIMIT 100
            """)
            recent_logs = cursor.fetchall()
            
            # Recent metrics
            cursor.execute("""
            SELECT * FROM system_metrics 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC 
            LIMIT 100
            """)
            recent_metrics = cursor.fetchall()
        
        return {
            'performance': asdict(performance),
            'active_alerts': [asdict(alert) for alert in active_alerts],
            'recent_logs': recent_logs,
            'recent_metrics': recent_metrics,
            'system_health': {
                'status': 'healthy' if not active_alerts else 'warning',
                'last_update': datetime.now().isoformat()
            }
        }

# Example usage
def main():
    """Example usage of the observability system."""
    obs = ObservabilitySystem()
    
    # Simulate some evaluation results
    evaluation_results = {
        'conversation_id': 'test-123',
        'trait_results': [
            {'trait': 'Collaborative', 'consensus_score': 4.0, 'confidence': 0.8},
            {'trait': 'Inquisitive', 'consensus_score': 4.0, 'confidence': 0.8}  # Same score - should trigger bias alert
        ],
        'metrics': type('Metrics', (), {
            'parsing_success_rate': 0.6,  # Low success rate - should trigger alert
            'evaluation_time': 35.0,  # Slow - should trigger alert
            'total_evaluations': 2
        })(),
        'bias_warnings': ['HIGH_TRAIT_CORRELATION_DETECTED']
    }
    
    # Monitor the evaluation
    obs.monitor_evaluation(evaluation_results)
    
    # Get dashboard data
    dashboard_data = obs.get_dashboard_data()
    print("Dashboard Data:")
    print(json.dumps(dashboard_data, indent=2, default=str))

if __name__ == "__main__":
    main()