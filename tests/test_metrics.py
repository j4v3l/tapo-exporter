"""Tests for the metrics module."""
import pytest

from tapo_exporter.metrics import TapoMetrics


@pytest.fixture
def metrics():
    """Create a TapoMetrics instance for testing."""
    return TapoMetrics()


def test_metrics_initialization(metrics):
    """Test that metrics are properly initialized."""
    assert metrics.device_count._type == "gauge"
    assert metrics.power_watts._type == "gauge"
    assert metrics.voltage_volts._type == "gauge"
    assert metrics.current_amps._type == "gauge"
    assert metrics.today_energy_wh._type == "gauge"
    assert metrics.monthly_energy_wh._type == "gauge"
    assert metrics.power_saved_wh._type == "gauge"
    assert metrics.today_runtime_minutes._type == "gauge"
    assert metrics.monthly_runtime_minutes._type == "gauge"
    assert metrics.power_protection_status._type == "gauge"
    assert metrics.overcurrent_protection_status._type == "gauge"
    assert metrics.overheat_protection_status._type == "gauge"
    assert metrics.signal_strength._type == "gauge"


@pytest.mark.asyncio
async def test_update_metrics(metrics):
    """Test updating metrics with sample data."""
    device_info = {
        "device_id": "test-device",
        "device_on": True,
        "power": 100.0,
        "voltage": 120.0,
        "current": 0.83,
        "today_energy": 500.0,
        "monthly_energy": 15000.0,
        "power_saved": 200.0,
        "today_runtime": 60,
        "monthly_runtime": 1800,
        "power_protection_status": True,
        "overcurrent_protection_status": False,
        "overheat_protection_status": False,
        "signal_strength": -50,
    }

    await metrics.update_metrics(device_info)

    assert metrics.device_count._value.get() == 1
    assert metrics.power_watts._value.get() == 100.0
    assert metrics.voltage_volts._value.get() == 120.0
    assert metrics.current_amps._value.get() == 0.83
    assert metrics.today_energy_wh._value.get() == 500.0
    assert metrics.monthly_energy_wh._value.get() == 15000.0
    assert metrics.power_saved_wh._value.get() == 200.0
    assert metrics.today_runtime_minutes._value.get() == 60
    assert metrics.monthly_runtime_minutes._value.get() == 1800
    assert metrics.power_protection_status._value.get() == 1
    assert metrics.overcurrent_protection_status._value.get() == 0
    assert metrics.overheat_protection_status._value.get() == 0
    assert metrics.signal_strength._value.get() == -50 