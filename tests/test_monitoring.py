import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import psutil
from monitoring.monitor_manager import (
    MetricsCollector, PerformanceTracker,
    AlertManager, MonitorManager
)

@pytest.fixture
def metrics_collector(mock_psutil):
    """Create MetricsCollector instance for testing"""
    with patch('monitoring.monitor_manager.psutil', mock_psutil):
        collector = MetricsCollector()
        # Mock the CPU percent to return exactly 50.0
        mock_psutil.cpu_percent.return_value = 50.0
        return collector

@pytest.fixture
def performance_tracker():
    """Create PerformanceTracker instance for testing"""
    return PerformanceTracker()

@pytest.fixture
def alert_manager(test_db):
    """Create AlertManager instance for testing"""
    with patch('monitoring.monitor_manager.db', test_db):
        manager = AlertManager()
        manager.notification_channels = ["test_channel"]
        # Mock the send_alert_notifications method
        manager.send_alert_notifications = AsyncMock()
        return manager

@pytest.fixture
def monitor_manager(metrics_collector, performance_tracker, alert_manager, test_db):
    """Create MonitorManager instance for testing"""
    with patch('monitoring.monitor_manager.db', test_db):
        manager = MonitorManager()
        manager.metrics_collector = metrics_collector
        manager.performance_tracker = performance_tracker
        manager.alert_manager = alert_manager
        return manager

@pytest.mark.asyncio
async def test_collect_system_metrics(metrics_collector):
    """Test system metrics collection"""
    metrics = await metrics_collector.collect_system_metrics()
    
    assert 'cpu_usage' in metrics
    assert 'memory_usage' in metrics
    assert 'disk_usage' in metrics
    assert 'timestamp' in metrics
    
    assert metrics['cpu_usage'] == 50.0  # From mock_psutil
    assert metrics['memory_usage'] == 60.0  # From mock_psutil
    assert metrics['disk_usage'] == 70.0  # From mock_psutil

    # Test error handling
    with patch.object(metrics_collector.psutil, 'cpu_percent', side_effect=Exception("CPU error")):
        with patch.object(metrics_collector.psutil, 'virtual_memory', side_effect=Exception("Memory error")):
            metrics = await metrics_collector.collect_system_metrics()
            assert metrics == {}

@pytest.mark.asyncio
async def test_performance_tracking(performance_tracker):
    """Test performance tracking functionality"""
    # Test command tracking
    await performance_tracker.track_command(
        command="test_command",
        execution_time=100.0,
        success=True
    )
    
    assert "test_command" in performance_tracker.command_timings
    assert len(performance_tracker.command_timings["test_command"]) == 1
    assert performance_tracker.request_counts["test_command"] == 1
    
    # Test failed command
    await performance_tracker.track_command(
        command="test_command",
        execution_time=150.0,
        success=False
    )
    
    assert performance_tracker.error_counts["test_command"] == 1
    assert performance_tracker.request_counts["test_command"] == 2
    
    # Test API call tracking
    await performance_tracker.track_api_call(
        endpoint="/test",
        latency=50.0,
        success=True
    )
    
    assert "/test" in performance_tracker.api_timings
    assert len(performance_tracker.api_timings["/test"]) == 1
    assert performance_tracker.request_counts["/test"] == 1

    # Test error handling with invalid inputs
    # Note: The code accepts empty strings as valid commands/endpoints
    await performance_tracker.track_command("", 100.0, True)
    assert "" in performance_tracker.command_timings
    assert len(performance_tracker.command_timings[""]) == 1

    await performance_tracker.track_api_call("", 50.0, True)
    assert "" in performance_tracker.api_timings
    assert len(performance_tracker.api_timings[""]) == 1

@pytest.mark.asyncio
async def test_alert_management(alert_manager):
    """Test alert management system"""
    # Test alert condition checking
    metrics = {
        'cpu_usage': 90.0,
        'memory_usage': 85.0,
        'api_latency': 2500.0
    }
    
    thresholds = {
        'cpu_usage': 80.0,
        'memory_usage': 80.0,
        'api_latency': 2000.0
    }
    
    alerts = await alert_manager.check_alert_conditions(metrics, thresholds)
    
    assert len(alerts) == 3
    assert any(a['type'] == 'cpu_usage' for a in alerts)
    assert any(a['type'] == 'memory_usage' for a in alerts)
    assert any(a['type'] == 'api_latency' for a in alerts)
    
    # Test alert processing
    alert = alerts[0]
    await alert_manager.process_alert(alert)
    
    assert len(alert_manager.active_alerts) == 1
    assert len(alert_manager.alert_history) == 1
    alert_manager.send_alert_notifications.assert_called_once_with(alert)

    # Test error handling
    with patch.dict(metrics, clear=True):
        alerts = await alert_manager.check_alert_conditions(metrics, thresholds)
        assert alerts == []

@pytest.mark.asyncio
async def test_monitor_manager(monitor_manager):
    """Test monitor manager functionality"""
    # Test monitoring start/stop
    await monitor_manager.start_monitoring()
    assert monitor_manager.monitoring_task is not None
    
    await monitor_manager.stop_monitoring()
    assert monitor_manager.monitoring_task is None
    
    # Test health check
    health = await monitor_manager.get_system_health()
    
    assert 'status' in health
    assert 'metrics' in health
    assert 'performance' in health
    assert 'active_alerts' in health

    # Test error handling in start_monitoring
    with patch('asyncio.create_task', side_effect=Exception("Task error")):
        await monitor_manager.start_monitoring()
        assert monitor_manager.monitoring_task is None

    # Test error handling in stop_monitoring
    monitor_manager.monitoring_task = MagicMock()
    monitor_manager.monitoring_task.cancel.side_effect = Exception("Cancel error")
    await monitor_manager.stop_monitoring()
    monitor_manager.monitoring_task = None  # Reset after test

@pytest.mark.asyncio
async def test_metrics_history(metrics_collector):
    """Test metrics history management"""
    # Add test metrics
    metrics_collector.metrics_history['cpu_usage'].append(50.0)
    metrics_collector.metrics_history['memory_usage'].append(60.0)
    
    assert len(metrics_collector.metrics_history['cpu_usage']) == 1
    assert len(metrics_collector.metrics_history['memory_usage']) == 1
    
    # Test maximum length enforcement
    for i in range(1000):
        metrics_collector.metrics_history['cpu_usage'].append(i)
    
    assert len(metrics_collector.metrics_history['cpu_usage']) == 1000

@pytest.mark.asyncio
async def test_alert_thresholds(metrics_collector):
    """Test alert threshold configuration"""
    thresholds = metrics_collector.alert_thresholds
    
    assert 'cpu_usage' in thresholds
    assert 'memory_usage' in thresholds
    assert 'api_latency' in thresholds
    assert 'error_rate' in thresholds
    
    assert thresholds['cpu_usage'] == 80.0
    assert thresholds['memory_usage'] == 80.0
    assert thresholds['api_latency'] == 2000.0
    assert thresholds['error_rate'] == 5.0

@pytest.mark.asyncio
async def test_performance_calculations(monitor_manager):
    """Test performance metric calculations"""
    # Add test data
    await monitor_manager.performance_tracker.track_command("cmd1", 100.0, True)
    await monitor_manager.performance_tracker.track_command("cmd1", 150.0, False)
    await monitor_manager.performance_tracker.track_command("cmd2", 200.0, True)
    
    await monitor_manager.performance_tracker.track_api_call("/api1", 50.0, True)
    await monitor_manager.performance_tracker.track_api_call("/api1", 75.0, False)
    await monitor_manager.performance_tracker.track_api_call("/api2", 100.0, True)
    
    # Test command latency calculation
    avg_cmd_latency = monitor_manager._calculate_avg_command_latency()
    assert avg_cmd_latency == 150.0  # (100 + 150 + 200) / 3

    # Test API latency calculation
    avg_api_latency = monitor_manager._calculate_avg_api_latency()
    assert avg_api_latency == 75.0  # (50 + 75 + 100) / 3

    # Test error rate calculation
    error_rate = monitor_manager._calculate_error_rate()
    assert error_rate == (2 / 6) * 100  # 2 errors out of 6 total requests

    # Test error handling
    with patch.dict(monitor_manager.performance_tracker.command_timings, clear=True):
        assert monitor_manager._calculate_avg_command_latency() == 0

    with patch.dict(monitor_manager.performance_tracker.api_timings, clear=True):
        assert monitor_manager._calculate_avg_api_latency() == 0

    with patch.dict(monitor_manager.performance_tracker.request_counts, clear=True):
        assert monitor_manager._calculate_error_rate() == 0

@pytest.mark.asyncio
async def test_alert_notifications(alert_manager):
    """Test alert notification system"""
    alert = {
        'type': 'test_alert',
        'severity': 'high',
        'message': 'Test alert message',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Process alert
    await alert_manager.process_alert(alert)
    
    # Verify alert was processed
    assert len(alert_manager.active_alerts) == 1
    assert len(alert_manager.alert_history) == 1
    alert_manager.send_alert_notifications.assert_called_once_with(alert)

    # Test error handling
    alert_manager.active_alerts.clear()  # Clear existing alerts
    with patch.object(alert_manager.db, 'table', side_effect=Exception("Database error")):
        await alert_manager.process_alert(alert)
        # Verify alert is still added to local storage even if DB fails
        assert len(alert_manager.active_alerts) == 1

@pytest.mark.asyncio
async def test_monitoring_loop(monitor_manager):
    """Test monitoring loop functionality"""
    # Mock the monitoring loop to avoid actual sleep
    with patch('asyncio.sleep', new_callable=AsyncMock):
        # Start monitoring
        await monitor_manager.start_monitoring()
        assert monitor_manager.monitoring_task is not None
        
        # Stop monitoring
        await monitor_manager.stop_monitoring()
        assert monitor_manager.monitoring_task is None

    # Test error handling in monitoring loop
    with patch('asyncio.sleep', side_effect=Exception("Loop error")):
        await monitor_manager._monitoring_loop()
        assert monitor_manager.monitoring_task is None

@pytest.mark.asyncio
async def test_store_metrics(monitor_manager, test_db):
    """Test metrics storage"""
    # Configure test_db mock
    test_db.table = MagicMock(return_value=test_db)
    test_db.insert = MagicMock(return_value=test_db)
    test_db.execute = AsyncMock()
    
    metrics = await monitor_manager.metrics_collector.collect_system_metrics()
    await monitor_manager._store_metrics(metrics)
    
    test_db.table.assert_called_with('metrics')
    test_db.insert.assert_called_once()
    test_db.execute.assert_called_once()

    # Test error handling
    test_db.execute.side_effect = Exception("Database error")
    await monitor_manager._store_metrics(metrics)  # Should not raise exception

@pytest.mark.asyncio
async def test_system_health_error_handling(monitor_manager):
    """Test error handling in system health check"""
    # Test metrics collection error
    with patch.object(monitor_manager.metrics_collector, 'collect_system_metrics',
                     side_effect=Exception("Metrics error")):
        health = await monitor_manager.get_system_health()
        assert health['status'] == 'error'
        assert 'message' in health

    # Test performance calculation errors
    with patch.object(monitor_manager, '_calculate_avg_command_latency',
                     side_effect=Exception("Latency error")):
        health = await monitor_manager.get_system_health()
        assert health['status'] == 'error'
        assert 'message' in health