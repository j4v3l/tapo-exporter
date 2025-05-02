"""Tests for the devices module."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tapo_exporter.devices.base import TapoDevice
from tapo_exporter.devices.p110 import P110Device


@pytest.fixture
def mock_device():
    """Create a mock Tapo device."""
    device = MagicMock(spec=TapoDevice)
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


@pytest.mark.asyncio
async def test_p110_device_initialization():
    """Test P110 device initialization."""
    device = P110Device(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        device_name="Test Device"
    )
    
    assert device.ip == "192.168.1.100"
    assert device.email == "test@example.com"
    assert device.password == "password"
    assert device.device_name == "Test Device"


@pytest.mark.asyncio
async def test_p110_device_connection():
    """Test P110 device connection."""
    with patch(
        "tapo_exporter.devices.p110.P110Device._connect"
    ) as mock_connect:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            device_name="Test Device"
        )
        
        mock_connect.return_value = AsyncMock()
        await device.connect()
        
        mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_p110_device_get_info():
    """Test P110 device get_info method."""
    with patch(
        "tapo_exporter.devices.p110.P110Device._connect"
    ) as mock_connect:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            device_name="Test Device"
        )
        
        mock_device = AsyncMock()
        mock_device.get_device_info.return_value = {
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
        
        mock_connect.return_value = mock_device
        await device.connect()
        
        info = await device.get_info()
        
        assert info["device_id"] == "test-device"
        assert info["device_on"] is True
        assert info["power"] == 100.0
        assert info["voltage"] == 120.0
        assert info["current"] == 0.83
        assert info["today_energy"] == 500.0
        assert info["monthly_energy"] == 15000.0
        assert info["power_saved"] == 200.0
        assert info["today_runtime"] == 60
        assert info["monthly_runtime"] == 1800
        assert info["power_protection_status"] is True
        assert info["overcurrent_protection_status"] is False
        assert info["overheat_protection_status"] is False
        assert info["signal_strength"] == -50 