"""
Monitoring service module for system monitoring functionality
"""
from typing import Dict, List
import psutil
from django.conf import settings

class MonitoringService:
    def __init__(self):
        self.cpu_threshold = settings.CPU_THRESHOLD
        self.memory_threshold = settings.MEMORY_THRESHOLD
        self.disk_threshold = settings.DISK_THRESHOLD

    def get_system_metrics(self) -> Dict:
        """
        Get current system metrics
        """
        return {
            'cpu': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
        }

    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        return psutil.cpu_percent(interval=1)

    def get_memory_usage(self) -> Dict:
        """Get memory usage statistics"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used,
            'free': memory.free
        }

    def get_disk_usage(self) -> Dict:
        """Get disk usage statistics"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }

    def check_alerts(self) -> List[Dict]:
        """
        Check system metrics against thresholds and return alerts
        """
        alerts = []
        metrics = self.get_system_metrics()

        if metrics['cpu'] > self.cpu_threshold:
            alerts.append({
                'type': 'cpu',
                'message': f'CPU usage ({metrics["cpu"]}%) exceeds threshold ({self.cpu_threshold}%)'
            })

        if metrics['memory']['percent'] > self.memory_threshold:
            alerts.append({
                'type': 'memory',
                'message': f'Memory usage ({metrics["memory"]["percent"]}%) exceeds threshold ({self.memory_threshold}%)'
            })

        if metrics['disk']['percent'] > self.disk_threshold:
            alerts.append({
                'type': 'disk',
                'message': f'Disk usage ({metrics["disk"]["percent"]}%) exceeds threshold ({self.disk_threshold}%)'
            })

        return alerts

monitoring_service = MonitoringService()