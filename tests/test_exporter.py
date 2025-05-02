"""Tests for the exporter module."""
from unittest.mock import MagicMock, patch

import pytest

from tapo_exporter.exporter import TapoExporter
from tapo_exporter.metrics import TapoMetrics


@pytest.fixture
def mock_exporter():
    """Create a mock Tapo exporter."""
    exporter = MagicMock(spec=TapoExporter)
    exporter.metrics = MagicMock()
    exporter.devices = []
    return exporter


@pytest.mark.asyncio
async def test_exporter_initialization():
    """Test exporter initialization."""
    exporter = TapoExporter()
    
    assert exporter.metrics is not None
    assert isinstance(exporter.metrics, TapoMetrics)
    assert exporter.devices == []


@pytest.mark.asyncio
async def test_exporter_add_device():
    """Test adding a device to the exporter."""
    exporter = TapoExporter()
    device = MagicMock()
    
    exporter.add_device(device)
    
    assert device in exporter.devices


@pytest.mark.asyncio
async def test_exporter_update_metrics():
    """Test updating metrics for all devices."""
    exporter = TapoExporter()
    device1 = MagicMock()
    device2 = MagicMock()
    
    device1.get_info.return_value = {
        "device_id": "device1",
        "device_on": True,
        "power": 100.0,
    }
    
    device2.get_info.return_value = {
        "device_id": "device2",
        "device_on": True,
        "power": 200.0,
    }
    
    exporter.add_device(device1)
    exporter.add_device(device2)
    
    await exporter.update_metrics()
    
    device1.get_info.assert_called_once()
    device2.get_info.assert_called_once()
    assert exporter.metrics.device_count._value.get() == 2


@pytest.mark.asyncio
async def test_exporter_start():
    """Test starting the exporter."""
    exporter = TapoExporter()
    
    with patch("asyncio.create_task") as mock_create_task:
        await exporter.start()
        
        mock_create_task.assert_called_once()
        assert exporter.running is True


@pytest.mark.asyncio
async def test_exporter_stop():
    """Test stopping the exporter."""
    exporter = TapoExporter()
    exporter.running = True
    
    await exporter.stop()
    
    assert exporter.running is False 