"""Tests for the devices module."""
from unittest.mock import AsyncMock, MagicMock, patch, call
import tempfile
import pytest

from tapo_exporter.devices.base import BaseTapoDevice
from tapo_exporter.devices.p110 import P110Device


class TestTapoDevice(BaseTapoDevice):
    """Concrete implementation of BaseTapoDevice for testing."""
    
    async def _get_device(self):
        """Get the device."""
        return MagicMock()
    
    async def get_device_info(self):
        """Get device info."""
        raise NotImplementedError()
    
    async def get_current_power(self):
        """Get current power."""
        raise NotImplementedError()
    
    async def get_device_usage(self):
        """Get device usage."""
        raise NotImplementedError()


@pytest.fixture
def mock_device():
    """Create a mock Tapo device."""
    device = MagicMock(spec=BaseTapoDevice)
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
async def test_base_device_initialization():
    """Test base device initialization."""
    device = TestTapoDevice(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    assert device.ip == "192.168.1.100"
    assert device.email == "test@example.com"
    assert device.password == "password"
    assert device.name == "Test Device"
    assert device.device is None


@pytest.mark.asyncio
async def test_base_device_connect_not_implemented():
    """Test that base device connect raises NotImplementedError."""
    device = TestTapoDevice(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    with pytest.raises(NotImplementedError):
        await device.get_device_info()


@pytest.mark.asyncio
async def test_base_device_get_info_not_implemented():
    """Test that base device get_info raises NotImplementedError."""
    device = TestTapoDevice(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    with pytest.raises(NotImplementedError):
        await device.get_device_info()


@pytest.mark.asyncio
async def test_base_device_get_current_power_not_implemented():
    """Test that base device get_current_power raises NotImplementedError."""
    device = TestTapoDevice(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    with pytest.raises(NotImplementedError):
        await device.get_current_power()


@pytest.mark.asyncio
async def test_base_device_get_device_usage_not_implemented():
    """Test that base device get_device_usage raises NotImplementedError."""
    device = TestTapoDevice(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    with pytest.raises(NotImplementedError):
        await device.get_device_usage()


@pytest.mark.asyncio
async def test_base_device_connect():
    """Test base device connect method."""
    device = TestTapoDevice(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    # Mock _get_device to return a mock device
    mock_dev = MagicMock()
    device._get_device = AsyncMock(return_value=mock_dev)
    
    # Connect to the device
    await device.connect()
    
    # Verify that _get_device was called and device was set
    device._get_device.assert_called_once()
    assert device.device == mock_dev


@pytest.mark.asyncio
async def test_base_device_connect_error():
    """Test base device connect error handling."""
    device = TestTapoDevice(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    # Mock _get_device to raise an exception
    device._get_device = AsyncMock(side_effect=Exception("Connection failed"))
    
    # Attempt to connect and expect an exception
    with pytest.raises(Exception) as exc_info:
        await device.connect()
    
    assert str(exc_info.value) == "Connection failed"
    device._get_device.assert_called_once()
    assert device.device is None


@pytest.mark.asyncio
async def test_base_device_reconnect():
    """Test base device reconnect functionality."""
    device = TestTapoDevice(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    # Mock _get_device to return a mock device
    mock_dev = MagicMock()
    device._get_device = AsyncMock(return_value=mock_dev)
    
    # Connect to the device
    await device.connect()
    
    # Verify initial connection
    device._get_device.assert_called_once()
    assert device.device == mock_dev
    
    # Reset the mock
    device._get_device.reset_mock()
    
    # Connect again
    await device.connect()
    
    # Verify that _get_device was called again
    device._get_device.assert_called_once()
    assert device.device == mock_dev


@pytest.mark.asyncio
async def test_base_device_turn_on():
    """Test turning on the device."""
    device = TestTapoDevice(
        name="Test Device",
        ip="192.168.1.100",
        email="test@example.com",
        password="password"
    )
    device.device = AsyncMock()
    await device.turn_on()
    device.device.on.assert_called_once()


@pytest.mark.asyncio
async def test_base_device_turn_off():
    """Test turning off the device."""
    device = TestTapoDevice(
        name="Test Device",
        ip="192.168.1.100",
        email="test@example.com",
        password="password"
    )
    device.device = AsyncMock()
    await device.turn_off()
    device.device.off.assert_called_once()


@pytest.mark.asyncio
async def test_base_device_turn_on_not_connected():
    """Test turning on the device when not connected."""
    device = TestTapoDevice(
        name="Test Device",
        ip="192.168.1.100",
        email="test@example.com",
        password="password"
    )
    device.device = None
    await device.turn_on()  # Should not raise an exception


@pytest.mark.asyncio
async def test_base_device_turn_off_not_connected():
    """Test turning off the device when not connected."""
    device = TestTapoDevice(
        name="Test Device",
        ip="192.168.1.100",
        email="test@example.com",
        password="password"
    )
    device.device = None
    await device.turn_off()  # Should not raise an exception


@pytest.mark.asyncio
async def test_base_device_is_connected():
    """Test is_connected property."""
    device = TestTapoDevice(
        name="Test Device",
        ip="192.168.1.100",
        email="test@example.com",
        password="password"
    )
    assert not device.is_connected
    device.device = AsyncMock()
    assert device.is_connected


@pytest.mark.asyncio
async def test_p110_device_initialization():
    """Test P110 device initialization."""
    device = P110Device(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    assert device.ip == "192.168.1.100"
    assert device.email == "test@example.com"
    assert device.password == "password"
    assert device.name == "Test Device"


@pytest.mark.asyncio
async def test_p110_device_connection():
    """Test P110 device connection."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        mock_client = AsyncMock()
        mock_p115 = AsyncMock()
        mock_device = AsyncMock()
        mock_device.get_device_info.return_value = MagicMock(
            model="P115",
            fw_ver="1.0.0"
        )
        mock_p115.return_value = mock_device
        mock_client.p115 = mock_p115
        mock_api_client.return_value = mock_client
        
        await device.connect()
        
        mock_api_client.assert_called_once_with(
            "test@example.com",
            "password"
        )
        mock_p115.assert_called_once_with("192.168.1.100")


@pytest.mark.asyncio
async def test_p110_device_get_info():
    """Test P110 device get_info method."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client and device
        mock_client = AsyncMock()
        mock_p115 = AsyncMock()
        mock_device = AsyncMock()
        
        # Set up the device info return value
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
        
        # Set up the mock chain
        mock_device.get_device_info.return_value = MagicMock(
            model="P115",
            fw_ver="1.0.0"
        )
        mock_device.get_device_info_json.return_value = device_info
        mock_p115.return_value = mock_device
        mock_client.p115 = mock_p115
        mock_api_client.return_value = mock_client
        
        # Connect to the device
        await device.connect()
        
        # Get device info
        info = await device.get_device_info()
        
        # Verify the results
        assert info == device_info
        mock_device.get_device_info_json.assert_called_once()
        mock_device.get_device_info.assert_called_once()
        mock_p115.assert_called_once_with("192.168.1.100")
        mock_api_client.assert_called_once_with(
            "test@example.com",
            "password"
        )


@pytest.mark.asyncio
async def test_p110_device_get_current_power():
    """Test P110 device get_current_power method."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client and device
        mock_client = AsyncMock()
        mock_p115 = AsyncMock()
        mock_device = AsyncMock()
        
        # Set up the power info return value
        power_info = {
            "current_power": 100.0,
            "voltage": 120.0,
            "current": 0.83
        }
        
        # Set up the mock chain
        mock_device.get_device_info.return_value = MagicMock(
            model="P115",
            fw_ver="1.0.0"
        )
        mock_device.get_current_power.return_value = power_info
        mock_p115.return_value = mock_device
        mock_client.p115 = mock_p115
        mock_api_client.return_value = mock_client
        
        # Connect to the device
        await device.connect()
        
        # Get current power
        power = await device.get_current_power()
        
        # Verify the results
        assert power == power_info
        mock_device.get_current_power.assert_called_once()


@pytest.mark.asyncio
async def test_p110_device_get_device_usage():
    """Test P110 device get_device_usage method."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client and device
        mock_client = AsyncMock()
        mock_p115 = AsyncMock()
        mock_device = AsyncMock()
        
        # Set up the usage info return value
        usage_info = {
            "today_energy": 500.0,
            "month_energy": 15000.0,
            "power_saved": 200.0,
            "today_runtime": 60,
            "month_runtime": 1800,
            "power_protection": True,
            "overcurrent_protection": False,
            "overheat_protection": False,
            "signal_strength": -50
        }
        
        # Set up the mock chain
        mock_device.get_device_info.return_value = MagicMock(
            model="P115",
            fw_ver="1.0.0"
        )
        mock_device.get_device_usage.return_value = usage_info
        mock_p115.return_value = mock_device
        mock_client.p115 = mock_p115
        mock_api_client.return_value = mock_client
        
        # Connect to the device
        await device.connect()
        
        # Get device usage
        usage = await device.get_device_usage()
        
        # Verify the results
        assert usage == usage_info
        mock_device.get_device_usage.assert_called_once()


@pytest.mark.asyncio
async def test_p110_device_connection_error():
    """Test P110 device connection error handling."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client to raise an exception
        mock_api_client.side_effect = Exception("Connection failed")
        
        # Attempt to connect and expect an exception
        with pytest.raises(Exception) as exc_info:
            await device.connect()
        
        assert str(exc_info.value) == "Connection failed"


@pytest.mark.asyncio
async def test_p110_device_get_info_error():
    """Test P110 device get_info error handling."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client and device
        mock_client = AsyncMock()
        mock_p115 = AsyncMock()
        mock_device = AsyncMock()
        
        # Set up the mock chain
        mock_device.get_device_info_json.side_effect = Exception("API error")
        mock_p115.return_value = mock_device
        mock_client.p115 = mock_p115
        mock_api_client.return_value = mock_client
        
        # Connect to the device
        await device.connect()
        
        # Attempt to get device info and expect an exception
        with pytest.raises(Exception) as exc_info:
            await device.get_device_info()
        
        assert str(exc_info.value) == "API error"
        mock_device.get_device_info_json.assert_called_once()


@pytest.mark.asyncio
async def test_p110_device_get_current_power_error():
    """Test P110 device get_current_power error handling."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client and device
        mock_client = AsyncMock()
        mock_p115 = AsyncMock()
        mock_device = AsyncMock()
        
        # Set up the mock chain
        mock_device.get_device_info.return_value = MagicMock(
            model="P115",
            fw_ver="1.0.0"
        )
        mock_device.get_current_power.side_effect = Exception("API error")
        mock_p115.return_value = mock_device
        mock_client.p115 = mock_p115
        mock_api_client.return_value = mock_client
        
        # Connect to the device
        await device.connect()
        
        # Attempt to get current power and expect an exception
        with pytest.raises(Exception) as exc_info:
            await device.get_current_power()
        
        assert str(exc_info.value) == "API error"
        mock_device.get_current_power.assert_called_once()


@pytest.mark.asyncio
async def test_p110_device_get_device_usage_error():
    """Test P110 device get_device_usage error handling."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client and device
        mock_client = AsyncMock()
        mock_p115 = AsyncMock()
        mock_device = AsyncMock()
        
        # Set up the mock chain
        mock_device.get_device_info.return_value = MagicMock(
            model="P115",
            fw_ver="1.0.0"
        )
        mock_device.get_device_usage.side_effect = Exception("API error")
        mock_p115.return_value = mock_device
        mock_client.p115 = mock_p115
        mock_api_client.return_value = mock_client
        
        # Connect to the device
        await device.connect()
        
        # Attempt to get device usage and expect an exception
        with pytest.raises(Exception) as exc_info:
            await device.get_device_usage()
        
        assert str(exc_info.value) == "API error"
        mock_device.get_device_usage.assert_called_once()


@pytest.mark.asyncio
async def test_p110_device_reconnect():
    """Test P110 device reconnect functionality."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client and device
        mock_client = AsyncMock()
        mock_p115 = AsyncMock()
        mock_device = AsyncMock()
        
        # Set up the mock chain
        mock_device.get_device_info.return_value = MagicMock(
            model="P115",
            fw_ver="1.0.0"
        )
        mock_p115.return_value = mock_device
        mock_client.p115 = mock_p115
        mock_api_client.return_value = mock_client
        
        # Connect to the device
        await device.connect()
        
        # Verify initial connection
        mock_p115.assert_called_once_with("192.168.1.100")
        assert device.device == mock_device
        
        # Reset the mock
        mock_p115.reset_mock()
        
        # Connect again
        await device.connect()
        
        # Verify that the device was reconnected
        mock_p115.assert_called_once_with("192.168.1.100")
        assert device.device == mock_device


@pytest.mark.asyncio
async def test_p110_device_clean_credentials():
    """Test P110 device credential cleanup."""
    with patch("tapo_exporter.devices.p110.glob") as mock_glob, \
         patch("tapo_exporter.devices.p110.os") as mock_os:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock glob.glob to return some test files
        mock_glob.glob.side_effect = [
            [tempfile.gettempdir() + "/tapo_1.json",
             tempfile.gettempdir() + "/tapo_2.json"],  # tmp files
            ["tapo_1.json", "tapo_2.json"]  # current dir files
        ]
        
        # Call _clean_credentials
        device._clean_credentials()
        
        # Verify that os.remove was called for each file
        assert mock_os.remove.call_count == 4
        mock_os.remove.assert_any_call(
            tempfile.gettempdir() + "/tapo_1.json"
        )
        mock_os.remove.assert_any_call(
            tempfile.gettempdir() + "/tapo_2.json"
        )
        mock_os.remove.assert_any_call("tapo_1.json")
        mock_os.remove.assert_any_call("tapo_2.json")


@pytest.mark.asyncio
async def test_p110_device_clean_credentials_error():
    """Test P110 device credential cleanup error handling."""
    with patch("tapo_exporter.devices.p110.glob") as mock_glob, \
         patch("tapo_exporter.devices.p110.os") as mock_os, \
         patch("tapo_exporter.devices.p110.logger") as mock_logger:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock glob.glob to return some test files
        mock_glob.glob.side_effect = [
            [tempfile.gettempdir() + "/tapo_1.json",
             tempfile.gettempdir() + "/tapo_2.json"],  # tmp files
            ["tapo_1.json", "tapo_2.json"]  # current dir files
        ]
        
        # Mock os.remove to raise an exception for one file
        mock_os.remove.side_effect = [
            None,  # First file removed successfully
            Exception("Failed to remove file"),  # Second file fails
            None,  # Third file removed successfully
            None   # Fourth file removed successfully
        ]
        
        # Call _clean_credentials
        device._clean_credentials()
        
        # Verify that os.remove was called for each file
        assert mock_os.remove.call_count == 4
        # Verify that the error was logged
        temp_file = tempfile.gettempdir() + "/tapo_2.json"
        error_msg = "Failed to remove {}: Failed to remove file"
        mock_logger.warning.assert_called_once_with(
            error_msg.format(temp_file)
        )


@pytest.mark.asyncio
async def test_p110_device_clean_credentials_current_dir_error():
    """Test P110 device credential cleanup error handling in current directory."""
    with patch("tapo_exporter.devices.p110.glob") as mock_glob, \
         patch("tapo_exporter.devices.p110.os") as mock_os, \
         patch("tapo_exporter.devices.p110.logger") as mock_logger:
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock glob.glob to return some test files
        mock_glob.glob.side_effect = [
            [],  # No tmp files
            ["tapo_1.json", "tapo_2.json"]  # current dir files
        ]
        
        # Mock os.remove to raise an exception for current dir file
        mock_os.remove.side_effect = Exception("Failed to remove file")
        
        # Call _clean_credentials
        device._clean_credentials()
        
        # Verify that os.remove was called for each file
        assert mock_os.remove.call_count == 2
        # Verify that the error was logged
        mock_logger.warning.assert_has_calls([
            call("Failed to remove tapo_1.json: Failed to remove file"),
            call("Failed to remove tapo_2.json: Failed to remove file")
        ])


@pytest.mark.asyncio
async def test_p110_device_connect_p110_first():
    """Test P110 device connection with P110 as first device type."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client, \
         patch("tapo_exporter.devices.p110.os.getenv", return_value="p110"):
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client and device
        mock_client = AsyncMock()
        mock_p110 = AsyncMock()
        mock_device = AsyncMock()
        
        # Set up the mock chain
        mock_p110.return_value = mock_device
        mock_client.p110 = mock_p110
        mock_api_client.return_value = mock_client
        
        # Set up device info response
        mock_device.get_device_info.return_value = MagicMock(
            model="P110",
            fw_ver="1.0.0"
        )
        
        # Connect to the device
        await device.connect()
        
        # Verify the connection attempt
        mock_p110.assert_called_once_with("192.168.1.100")
        mock_device.get_device_info.assert_called_once()
        assert device.device == mock_device


@pytest.mark.asyncio
async def test_p110_device_not_connected_errors():
    """Test error handling when device is not connected."""
    device = P110Device(
        ip="192.168.1.100",
        email="test@example.com",
        password="password",
        name="Test Device"
    )
    
    # Test get_device_info without connection
    with pytest.raises(RuntimeError) as exc_info:
        await device.get_device_info()
    assert str(exc_info.value) == "Device not connected"
    
    # Test get_current_power without connection
    with pytest.raises(RuntimeError) as exc_info:
        await device.get_current_power()
    assert str(exc_info.value) == "Device not connected"
    
    # Test get_device_usage without connection
    with pytest.raises(RuntimeError) as exc_info:
        await device.get_device_usage()
    assert str(exc_info.value) == "Device not connected"


@pytest.mark.asyncio
async def test_p110_device_connect_alternative_type():
    """Test P110 device connection with alternative device type."""
    with patch("tapo_exporter.devices.p110.ApiClient") as mock_api_client, \
         patch("tapo_exporter.devices.p110.os.getenv", return_value="p110"), \
         patch("tapo_exporter.devices.p110.time.sleep"):
        device = P110Device(
            ip="192.168.1.100",
            email="test@example.com",
            password="password",
            name="Test Device"
        )
        
        # Mock the API client and device
        mock_client = AsyncMock()
        mock_p110 = AsyncMock()
        mock_p115 = AsyncMock()
        mock_device = AsyncMock()
        
        # Set up the mock chain for initial failure and alternative success
        mock_p110.side_effect = Exception("P110 connection failed")
        mock_p115.return_value = mock_device
        mock_client.p110 = mock_p110
        mock_client.p115 = mock_p115
        mock_api_client.return_value = mock_client
        
        # Set up device info response
        mock_device.get_device_info.return_value = MagicMock(
            model="P115",
            fw_ver="1.0.0"
        )
        
        # Connect to the device
        await device.connect()
        
        # Verify the connection attempts
        mock_p110.assert_called_once_with("192.168.1.100")
        mock_p115.assert_called_once_with("192.168.1.100")
        mock_device.get_device_info.assert_called_once()
        assert device.device == mock_device 