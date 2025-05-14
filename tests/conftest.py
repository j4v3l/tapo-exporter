"""Test configuration file."""

from unittest.mock import MagicMock
import pytest
from tapo_exporter.exporter import TapoExporter
from tapo_exporter.metrics import TapoMetrics


@pytest.fixture
def metrics():
    """Create a TapoMetrics instance for testing."""
    return TapoMetrics()


@pytest.fixture
def exporter():
    """Create a TapoExporter instance for testing."""
    return TapoExporter()


@pytest.fixture
def mock_device():
    """Create a mock Tapo device."""
    device = MagicMock()
    device.device_id = "test-device"
    device.device_on = True
    device.power = 100.0
    device.voltage = 120.0
    device.current = 0.83
    device.today_energy = 500.0
    device.monthly_energy = 15000.0
    device.power_saved = 200.0
    device.today_runtime = 60
    device.monthly_runtime = 1800
    device.power_protection_status = True
    device.overcurrent_protection_status = False
    device.overheat_protection_status = False
    device.signal_strength = -50
    return device


@pytest.fixture
def mock_exporter():
    """Create a mock Tapo exporter."""
    exporter = MagicMock(spec=TapoExporter)
    exporter.metrics = MagicMock(spec=TapoMetrics)
    exporter.devices = []
    return exporter
