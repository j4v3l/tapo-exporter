"""Tests for the metrics module."""
from unittest.mock import MagicMock, AsyncMock
from unittest.mock import patch

import pytest
from prometheus_client import CollectorRegistry

from tapo_exporter.metrics import TapoMetrics


@pytest.fixture
def registry():
    """Create a new registry for each test."""
    return CollectorRegistry()


@pytest.fixture
def metrics(registry):
    """Create a TapoMetrics instance for testing."""
    return TapoMetrics(registry=registry)


def test_metrics_initialization(metrics):
    """Test metrics initialization."""
    assert metrics.device_count is not None
    assert metrics.power_watts is not None
    assert metrics.voltage_volts is not None
    assert metrics.current_amps is not None
    assert metrics.calculated_current_amps is not None
    assert metrics.today_energy_wh is not None
    assert metrics.month_energy_wh is not None
    assert metrics.power_saved_wh is not None
    assert metrics.today_runtime_minutes is not None
    assert metrics.month_runtime_minutes is not None
    assert metrics.power_protection_status is not None
    assert metrics.overcurrent_status is not None
    assert metrics.overheat_status is not None
    assert metrics.signal_rssi is not None


@pytest.mark.asyncio
async def test_update_metrics(metrics):
    """Test updating metrics."""
    mock_device = MagicMock()
    mock_device.name = "Test Device"
    
    # Mock device info as an object with attributes
    mock_device_info = MagicMock()
    mock_device_info.nickname = "Test Device"
    mock_device_info.model = "p110"
    mock_device.get_device_info = AsyncMock(return_value=mock_device_info)
    
    # Mock power info as an object with attributes
    mock_power_info = MagicMock()
    mock_power_info.current_power = 100.0
    mock_power_info.voltage = 120.0
    mock_power_info.current = 0.83
    mock_device.get_current_power = AsyncMock(return_value=mock_power_info)
    
    # Mock usage info as an object with attributes
    mock_usage_info = MagicMock()
    mock_usage_info.today_energy = 500.0
    mock_usage_info.month_energy = 15000.0
    mock_usage_info.power_saved = 200.0
    mock_usage_info.today_runtime = 60
    mock_usage_info.month_runtime = 1800
    mock_usage_info.power_protection = True
    mock_usage_info.overcurrent_protection = False
    mock_usage_info.overheat_protection = False
    mock_usage_info.signal_strength = -50
    mock_device.get_device_usage = AsyncMock(return_value=mock_usage_info)

    await metrics.update_metrics(mock_device)

    # Define expected labels
    labels = {"device_name": "Test Device", "device_type": "p110"}

    # Helper function to get metric value
    def get_value(metric):
        samples = [
            s for s in metric.collect()[0].samples if s.labels == labels
        ]
        return samples[0].value if samples else None

    # Check power metrics
    assert get_value(metrics.power_watts) == 100.0
    assert get_value(metrics.voltage_volts) == 120.0
    assert get_value(metrics.current_amps) == 0.83
    assert get_value(metrics.calculated_current_amps) == 100.0 / 120.0

    # Check usage metrics
    assert get_value(metrics.today_energy_wh) == 500.0
    assert get_value(metrics.month_energy_wh) == 15000.0
    assert get_value(metrics.power_saved_wh) == 200.0
    assert get_value(metrics.today_runtime_minutes) == 60
    assert get_value(metrics.month_runtime_minutes) == 1800

    # Check protection status
    assert get_value(metrics.power_protection_status) == 1
    assert get_value(metrics.overcurrent_status) == 0
    assert get_value(metrics.overheat_status) == 0

    # Check signal strength
    assert get_value(metrics.signal_rssi) == -50


@pytest.mark.asyncio
async def test_metrics_invalid_voltage(metrics):
    """Test metrics update with invalid voltage."""
    mock_device = MagicMock()
    mock_device.name = "Test Device"
    mock_device.ip = "192.168.1.100"

    # Mock device info as an object with attributes
    mock_device_info = MagicMock()
    mock_device_info.nickname = "Test Device"
    mock_device_info.model = "P110"
    mock_device.get_device_info = AsyncMock(return_value=mock_device_info)

    # Mock power info with zero voltage
    mock_power_info = MagicMock()
    mock_power_info.current_power = 100.0
    mock_power_info.voltage = 0.0
    mock_power_info.current = 0.5
    mock_device.get_current_power = AsyncMock(return_value=mock_power_info)

    # Mock usage info as an object with attributes
    mock_usage_info = MagicMock()
    mock_usage_info.today_energy = 1000.0
    mock_usage_info.month_energy = 30000.0
    mock_usage_info.power_saved = 500.0
    mock_usage_info.today_runtime = 120
    mock_usage_info.month_runtime = 3600
    mock_usage_info.power_protection = True
    mock_usage_info.overcurrent_protection = False
    mock_usage_info.overheat_protection = True
    mock_usage_info.signal_strength = -65
    mock_device.get_device_usage = AsyncMock(return_value=mock_usage_info)

    # Update metrics
    with patch("tapo_exporter.metrics.logger") as mock_logger:
        await metrics.update_metrics(mock_device)

        # Verify debug message was logged for voltage
        expected_msg = (
            f"Device {mock_device.name} does not support voltage monitoring "
            f"(power: {mock_power_info.current_power} W)"
        )
        mock_logger.debug.assert_called_with(expected_msg)


@pytest.mark.asyncio
async def test_metrics_update_error():
    """Test error handling in metrics update."""
    metrics = TapoMetrics()
    mock_device = MagicMock()
    mock_device.name = "Test Device"
    mock_device.ip = "192.168.1.100"
    
    # Mock device info to raise an exception
    mock_device.get_device_info = AsyncMock(
        side_effect=Exception("Test error")
    )
    
    # Update metrics
    with patch("tapo_exporter.metrics.logger") as mock_logger:
        await metrics.update_metrics(mock_device)
        
        # Verify error was logged
        expected_msg = (
            "Error updating metrics for device 192.168.1.100: Test error"
        )
        mock_logger.error.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
async def test_metrics_missing_device_info():
    """Test metrics update with missing device info."""
    metrics = TapoMetrics()
    mock_device = MagicMock()
    mock_device.name = "Test Device"
    mock_device.ip = "192.168.1.100"
    
    # Mock device info to return None
    mock_device.get_device_info = AsyncMock(return_value=None)
    
    # Update metrics
    with patch("tapo_exporter.metrics.logger") as mock_logger:
        await metrics.update_metrics(mock_device)
        
        # Verify warning was logged
        expected_msg = (
            "Failed to get device info for Test Device. "
            "Skipping metrics update."
        )
        mock_logger.warning.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
async def test_metrics_missing_power_info():
    """Test metrics update with missing power info."""
    metrics = TapoMetrics()
    mock_device = MagicMock()
    mock_device.name = "Test Device"
    mock_device.ip = "192.168.1.100"
    
    # Mock device info
    mock_device.get_device_info = AsyncMock(return_value={
        "nickname": "Test Device",
        "model": "P110"
    })
    
    # Mock power info to return None
    mock_device.get_current_power = AsyncMock(return_value=None)
    
    # Update metrics
    with patch("tapo_exporter.metrics.logger") as mock_logger:
        await metrics.update_metrics(mock_device)
        
        # Verify warning was logged
        expected_msg = (
            "Failed to get power info for Test Device. "
            "Skipping metrics update."
        )
        mock_logger.warning.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
async def test_metrics_missing_usage_info(metrics):
    """Test metrics update with missing usage info."""
    mock_device = MagicMock()
    mock_device.name = "Test Device"
    mock_device.ip = "192.168.1.100"
    
    # Mock device info
    mock_device.get_device_info = AsyncMock(return_value={
        "nickname": "Test Device",
        "model": "P110"
    })
    
    # Mock power info
    mock_device.get_current_power = AsyncMock(return_value={
        "current_power": 100,
        "voltage": 120,
        "current": 0.5
    })
    
    # Mock usage info to return None
    mock_device.get_device_usage = AsyncMock(return_value=None)
    
    # Update metrics
    with patch("tapo_exporter.metrics.logger") as mock_logger:
        await metrics.update_metrics(mock_device)
        
        # Verify warning was logged
        expected_msg = (
            "Failed to get usage info for Test Device. "
            "Skipping usage metrics update."
        )
        mock_logger.warning.assert_called_once_with(expected_msg)


@pytest.mark.asyncio
async def test_metrics_invalid_power_values(metrics):
    """Test metrics update with invalid power values."""
    mock_device = MagicMock()
    mock_device.name = "Test Device"
    mock_device.ip = "192.168.1.100"

    # Mock device info as an object with attributes
    mock_device_info = MagicMock()
    mock_device_info.nickname = "Test Device"
    mock_device_info.model = "P110"
    mock_device.get_device_info = AsyncMock(return_value=mock_device_info)

    # Mock power info with invalid values
    mock_power_info = MagicMock()
    mock_power_info.current_power = -100.0  # Invalid negative power
    mock_power_info.voltage = -120.0  # Invalid negative voltage
    mock_power_info.current = -0.5  # Invalid negative current
    mock_device.get_current_power = AsyncMock(return_value=mock_power_info)

    # Mock usage info as an object with attributes
    mock_usage_info = MagicMock()
    mock_usage_info.today_energy = -1000.0  # Invalid negative energy
    mock_usage_info.month_energy = -30000.0  # Invalid negative energy
    mock_usage_info.power_saved = -500.0  # Invalid negative power saved
    mock_usage_info.today_runtime = -120  # Invalid negative runtime
    mock_usage_info.month_runtime = -3600  # Invalid negative runtime
    mock_usage_info.power_protection = True
    mock_usage_info.overcurrent_protection = False
    mock_usage_info.overheat_protection = True
    mock_usage_info.signal_strength = -65
    mock_device.get_device_usage = AsyncMock(return_value=mock_usage_info)

    # Update metrics
    await metrics.update_metrics(mock_device)

    # Verify metrics were updated with absolute values
    labels = {"device_name": "Test Device", "device_type": "p110"}

    def get_value(metric):
        samples = [
            s for s in metric.collect()[0].samples if s.labels == labels
        ]
        return samples[0].value if samples else None

    # Check power metrics
    assert get_value(metrics.power_watts) == 100.0
    assert get_value(metrics.voltage_volts) == 120.0
    assert get_value(metrics.current_amps) == 0.5

    # Check usage metrics
    assert get_value(metrics.today_energy_wh) == 1000.0
    assert get_value(metrics.month_energy_wh) == 30000.0
    assert get_value(metrics.power_saved_wh) == 500.0
    assert get_value(metrics.today_runtime_minutes) == 120
    assert get_value(metrics.month_runtime_minutes) == 3600