from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import psutil
from collections import deque
from config import settings
from utils.logger import logger
from database.supabase_client import db

class MetricsCollector:
    """Collects and manages system metrics"""
    def __init__(self, psutil_instance=None):
        self.metrics_history = {
            'cpu_usage': deque(maxlen=1000),
            'memory_usage': deque(maxlen=1000),
            'api_latency': deque(maxlen=1000),
            'command_latency': deque(maxlen=1000),
            'error_count': deque(maxlen=1000)
        }
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 80.0,
            'api_latency': 2000.0,
            'error_rate': 5.0
        }
        self.psutil = psutil_instance or psutil

    async def collect_system_metrics(self) -> Dict:
        """Collect current system metrics"""
        try:
            cpu_percent = self.psutil.cpu_percent()
            memory = self.psutil.virtual_memory()
            
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available,
                'disk_usage': self.psutil.disk_usage('/').percent
            }
            
            # Update history
            self.metrics_history['cpu_usage'].append(cpu_percent)
            self.metrics_history['memory_usage'].append(memory.percent)
            
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")
            return {}

class PerformanceTracker:
    """Tracks application performance metrics"""
    def __init__(self):
        self.command_timings = {}
        self.api_timings = {}
        self.error_counts = {}
        self.request_counts = {}

    async def track_command(
        self,
        command: str,
        execution_time: float,
        success: bool
    ) -> None:
        """Track command execution metrics"""
        try:
            if command not in self.command_timings:
                self.command_timings[command] = []
            
            self.command_timings[command].append(execution_time)
            
            if not success:
                self.error_counts[command] = self.error_counts.get(command, 0) + 1
            
            self.request_counts[command] = self.request_counts.get(command, 0) + 1

        except Exception as e:
            logger.error(f"Failed to track command: {str(e)}")

    async def track_api_call(
        self,
        endpoint: str,
        latency: float,
        success: bool
    ) -> None:
        """Track API call metrics"""
        try:
            if endpoint not in self.api_timings:
                self.api_timings[endpoint] = []
            
            self.api_timings[endpoint].append(latency)
            
            if not success:
                self.error_counts[endpoint] = self.error_counts.get(endpoint, 0) + 1
            
            self.request_counts[endpoint] = self.request_counts.get(endpoint, 0) + 1

        except Exception as e:
            logger.error(f"Failed to track API call: {str(e)}")

class AlertManager:
    """Manages system alerts and notifications"""
    def __init__(self, db_instance=None):
        self.active_alerts = {}
        self.alert_history = []
        self.notification_channels = []
        self.db = db_instance or db

    async def check_alert_conditions(
        self,
        metrics: Dict,
        thresholds: Dict
    ) -> List[Dict]:
        """Check for alert conditions"""
        try:
            alerts = []
            
            # Check CPU usage
            if metrics.get('cpu_usage', 0) > thresholds['cpu_usage']:
                alerts.append({
                    'type': 'cpu_usage',
                    'severity': 'high',
                    'message': f"CPU usage is {metrics['cpu_usage']}%",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check memory usage
            if metrics.get('memory_usage', 0) > thresholds['memory_usage']:
                alerts.append({
                    'type': 'memory_usage',
                    'severity': 'high',
                    'message': f"Memory usage is {metrics['memory_usage']}%",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Check API latency
            if metrics.get('api_latency', 0) > thresholds['api_latency']:
                alerts.append({
                    'type': 'api_latency',
                    'severity': 'medium',
                    'message': f"High API latency: {metrics['api_latency']}ms",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return alerts

        except Exception as e:
            logger.error(f"Failed to check alert conditions: {str(e)}")
            return []

    async def process_alert(self, alert: Dict) -> None:
        """Process and store alert"""
        try:
            alert_id = f"{alert['type']}_{alert['timestamp']}"
            
            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Save to database
            if self.db and hasattr(self.db, 'table'):
                await self.db.table('alerts').insert(alert).execute()
            
            # Send notifications
            await self.send_alert_notifications(alert)

        except Exception as e:
            logger.error(f"Failed to process alert: {str(e)}")

    async def send_alert_notifications(self, alert: Dict) -> None:
        """Send alert notifications to configured channels"""
        try:
            for channel in self.notification_channels:
                # Implementation would depend on notification channel type
                # (Discord, Email, SMS, etc.)
                pass

        except Exception as e:
            logger.error(f"Failed to send alert notifications: {str(e)}")

class MonitorManager:
    """Main monitoring system manager"""
    def __init__(self, db_instance=None, psutil_instance=None):
        self.metrics_collector = MetricsCollector(psutil_instance)
        self.performance_tracker = PerformanceTracker()
        self.alert_manager = AlertManager(db_instance)
        self.monitoring_task = None
        self.db = db_instance or db

    async def start_monitoring(self) -> None:
        """Start the monitoring system"""
        try:
            if not self.monitoring_task:
                self.monitoring_task = asyncio.create_task(self._monitoring_loop())
                logger.info("Monitoring system started")
        except Exception as e:
            logger.error(f"Failed to start monitoring: {str(e)}")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring system"""
        try:
            if self.monitoring_task:
                self.monitoring_task.cancel()
                self.monitoring_task = None
                logger.info("Monitoring system stopped")
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {str(e)}")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        try:
            while True:
                # Collect metrics
                metrics = await self.metrics_collector.collect_system_metrics()
                
                # Check for alerts
                alerts = await self.alert_manager.check_alert_conditions(
                    metrics,
                    self.metrics_collector.alert_thresholds
                )
                
                # Process alerts
                for alert in alerts:
                    await self.alert_manager.process_alert(alert)
                
                # Store metrics
                await self._store_metrics(metrics)
                
                # Wait for next collection interval
                await asyncio.sleep(settings.MONITORING_INTERVAL)

        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            self.monitoring_task = None

    async def _store_metrics(self, metrics: Dict) -> None:
        """Store metrics in database"""
        try:
            if self.db and hasattr(self.db, 'table'):
                await self.db.table('metrics').insert(metrics).execute()
        except Exception as e:
            logger.error(f"Failed to store metrics: {str(e)}")

    async def get_system_health(self) -> Dict:
        """Get current system health status"""
        try:
            metrics = await self.metrics_collector.collect_system_metrics()
            
            return {
                'status': 'healthy' if not self.alert_manager.active_alerts else 'warning',
                'metrics': metrics,
                'active_alerts': list(self.alert_manager.active_alerts.values()),
                'performance': {
                    'avg_command_latency': self._calculate_avg_command_latency(),
                    'avg_api_latency': self._calculate_avg_api_latency(),
                    'error_rate': self._calculate_error_rate()
                }
            }

        except Exception as e:
            logger.error(f"Failed to get system health: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def _calculate_avg_command_latency(self) -> float:
        """Calculate average command latency"""
        try:
            all_latencies = []
            for timings in self.performance_tracker.command_timings.values():
                all_latencies.extend(timings)
            return sum(all_latencies) / len(all_latencies) if all_latencies else 0
        except Exception as e:
            logger.error(f"Failed to calculate average command latency: {str(e)}")
            return 0

    def _calculate_avg_api_latency(self) -> float:
        """Calculate average API latency"""
        try:
            all_latencies = []
            for timings in self.performance_tracker.api_timings.values():
                all_latencies.extend(timings)
            return sum(all_latencies) / len(all_latencies) if all_latencies else 0
        except Exception as e:
            logger.error(f"Failed to calculate average API latency: {str(e)}")
            return 0

    def _calculate_error_rate(self) -> float:
        """Calculate overall error rate"""
        try:
            total_requests = sum(self.performance_tracker.request_counts.values())
            total_errors = sum(self.performance_tracker.error_counts.values())
            return (total_errors / total_requests * 100) if total_requests > 0 else 0
        except Exception as e:
            logger.error(f"Failed to calculate error rate: {str(e)}")
            return 0

# Initialize monitoring manager
monitor_manager = MonitorManager()