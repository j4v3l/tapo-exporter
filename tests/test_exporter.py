"""Test the TapoExporter class."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tapo_exporter.exporter import TapoExporter


@pytest.fixture
def mock_devices():
    """Create mock devices for testing."""
    return []


@pytest.fixture
def mock_influx_client():
    """Create a mock InfluxDB client."""
    with patch("tapo_exporter.exporter.InfluxDBClient") as mock_client:
        mock_write_api = MagicMock()
        mock_client.return_value.write_api.return_value = mock_write_api
        yield mock_client


@pytest.mark.asyncio
async def test_exporter_initialization(mock_devices, mock_influx_client):
    """Test exporter initialization."""
    exporter = TapoExporter(devices=mock_devices)
    assert len(exporter.devices) == 0
    assert exporter.metrics is not None
    assert exporter.influx_client is not None
    assert exporter.write_api is not None


@pytest.mark.asyncio
async def test_exporter_add_device(mock_devices, mock_influx_client):
    """Test adding a device to the exporter."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    exporter.add_device(mock_device)
    assert len(exporter.devices) == 1
    assert exporter.devices[0] == mock_device


@pytest.mark.asyncio
async def test_exporter_update_metrics(mock_devices, mock_influx_client):
    """Test updating metrics."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=120,
        current=1000,
        power_factor=0.9
    ))
    mock_device.get_device_usage = AsyncMock(return_value=MagicMock(
        today_energy=1000,
        month_energy=10000,
        today_runtime=60,
        month_runtime=600,
        power_saved=100,
        power_protection=False,
        overcurrent_protection=False,
        overheat_protection=False,
        signal_strength=80
    ))
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_update_metrics_error(mock_devices, mock_influx_client):
    """Test error handling during metrics update."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = None
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_connect_devices(mock_devices, mock_influx_client):
    """Test connecting to devices."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.connect = AsyncMock()
    exporter.add_device(mock_device)
    await exporter.connect_devices()
    mock_device.connect.assert_called_once()


@pytest.mark.asyncio
async def test_exporter_connect_devices_error(mock_devices, mock_influx_client):
    """Test error handling during device connection."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.connect = AsyncMock(side_effect=Exception("Connection failed"))
    exporter.add_device(mock_device)
    await exporter.connect_devices()  # Should not raise exception


@pytest.mark.asyncio
async def test_exporter_start(mock_devices, mock_influx_client):
    """Test starting the exporter."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=120,
        current=1000,
        power_factor=0.9
    ))
    mock_device.get_device_usage = AsyncMock(return_value=MagicMock(
        today_energy=1000,
        month_energy=10000,
        today_runtime=60,
        month_runtime=600,
        power_saved=100,
        power_protection=False,
        overcurrent_protection=False,
        overheat_protection=False,
        signal_strength=80
    ))
    exporter.add_device(mock_device)
    
    # Create a task that will cancel after a short delay
    task = asyncio.create_task(exporter.start())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_exporter_start_error(mock_devices, mock_influx_client):
    """Test error handling during exporter start."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(side_effect=Exception("Test error"))
    exporter.add_device(mock_device)
    
    # Create a task that will cancel after a short delay
    task = asyncio.create_task(exporter.start())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_exporter_stop(mock_devices, mock_influx_client):
    """Test stopping the exporter."""
    exporter = TapoExporter(devices=mock_devices)
    await exporter.stop()
    mock_influx_client.return_value.close.assert_called_once()


@pytest.mark.asyncio
async def test_exporter_update_metrics_device_not_connected(
    mock_devices, mock_influx_client
):
    """Test updating metrics when device is not connected."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = None
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_update_metrics_failed_device_info(
    mock_devices, mock_influx_client
):
    """Test handling failed device info retrieval."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value=None)
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_update_metrics_failed_power_info(
    mock_devices, mock_influx_client
):
    """Test handling failed power info retrieval."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=None)
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_update_metrics_failed_usage_info(
    mock_devices, mock_influx_client
):
    """Test handling failed usage info retrieval."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=120,
        current=1000,
        power_factor=0.9
    ))
    mock_device.get_device_usage = AsyncMock(return_value=None)
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_start_error_handling(mock_influx_client):
    """Test error handling in start method."""
    with patch("tapo_exporter.exporter.logger") as mock_logger:
        exporter = TapoExporter()
        mock_device = MagicMock()
        mock_device.name = "test_device"
        mock_device.device = MagicMock()
        mock_device.get_device_info = AsyncMock(
            side_effect=Exception("Test error")
        )
        exporter.add_device(mock_device)
        
        # Create a task that will cancel after a short delay
        task = asyncio.create_task(exporter.start())
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_exporter_update_metrics_with_invalid_voltage(
    mock_devices, mock_influx_client
):
    """Test updating metrics with invalid voltage value."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=-1,  # Invalid voltage
        current=1000,
        power_factor=0.9
    ))
    mock_device.get_device_usage = AsyncMock(return_value=MagicMock(
        today_energy=1000,
        month_energy=10000,
        today_runtime=60,
        month_runtime=600,
        power_saved=100,
        power_protection=False,
        overcurrent_protection=False,
        overheat_protection=False,
        signal_strength=80
    ))
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_update_metrics_with_invalid_current(
    mock_devices, mock_influx_client
):
    """Test updating metrics with invalid current value."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=120,
        current=-1,  # Invalid current
        power_factor=0.9
    ))
    mock_device.get_device_usage = AsyncMock(return_value=MagicMock(
        today_energy=1000,
        month_energy=10000,
        today_runtime=60,
        month_runtime=600,
        power_saved=100,
        power_protection=False,
        overcurrent_protection=False,
        overheat_protection=False,
        signal_strength=80
    ))
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_update_metrics_with_invalid_power_factor(
    mock_devices, mock_influx_client
):
    """Test updating metrics with invalid power factor value."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=120,
        current=1000,
        power_factor=2.0  # Invalid power factor
    ))
    mock_device.get_device_usage = AsyncMock(return_value=MagicMock(
        today_energy=1000,
        month_energy=10000,
        today_runtime=60,
        month_runtime=600,
        power_saved=100,
        power_protection=False,
        overcurrent_protection=False,
        overheat_protection=False,
        signal_strength=80
    ))
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_update_metrics_with_invalid_signal_strength(
    mock_devices, mock_influx_client
):
    """Test updating metrics with invalid signal strength value."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=120,
        current=1000,
        power_factor=0.9
    ))
    mock_device.get_device_usage = AsyncMock(return_value=MagicMock(
        today_energy=1000,
        month_energy=10000,
        today_runtime=60,
        month_runtime=600,
        power_saved=100,
        power_protection=False,
        overcurrent_protection=False,
        overheat_protection=False,
        signal_strength=-1  # Invalid signal strength
    ))
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_update_metrics_with_invalid_runtime(
    mock_devices, mock_influx_client
):
    """Test updating metrics with invalid runtime value."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=120,
        current=1000,
        power_factor=0.9
    ))
    mock_device.get_device_usage = AsyncMock(return_value=MagicMock(
        today_energy=1000,
        month_energy=10000,
        today_runtime=-1,  # Invalid runtime
        month_runtime=600,
        power_saved=100,
        power_protection=False,
        overcurrent_protection=False,
        overheat_protection=False,
        signal_strength=80
    ))
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_update_metrics_with_invalid_energy(
    mock_devices, mock_influx_client
):
    """Test updating metrics with invalid energy value."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"model": "test"})
    mock_device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=120,
        current=1000,
        power_factor=0.9
    ))
    mock_device.get_device_usage = AsyncMock(return_value=MagicMock(
        today_energy=-1,  # Invalid energy
        month_energy=10000,
        today_runtime=60,
        month_runtime=600,
        power_saved=100,
        power_protection=False,
        overcurrent_protection=False,
        overheat_protection=False,
        signal_strength=80
    ))
    exporter.add_device(mock_device)
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_cleanup_on_error(mock_devices, mock_influx_client):
    """Test exporter cleanup when an error occurs."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.clean_credentials = AsyncMock(
        side_effect=Exception("Cleanup failed")
    )
    exporter.add_device(mock_device)
    
    await exporter.stop()
    mock_influx_client.return_value.close.assert_called_once()


@pytest.mark.asyncio
async def test_exporter_initialization_with_invalid_config(mock_devices):
    """Test exporter initialization with invalid configuration."""
    with patch("tapo_exporter.exporter.InfluxDBClient") as mock_client:
        mock_client.side_effect = Exception("Invalid config")
        with pytest.raises(Exception):
            TapoExporter(devices=mock_devices)


@pytest.mark.asyncio
async def test_exporter_device_connection_error_handling(
    mock_devices, mock_influx_client
):
    """Test error handling during device connection."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.connect = AsyncMock(side_effect=Exception("Connection failed"))
    exporter.add_device(mock_device)
    
    await exporter.connect_devices()
    mock_device.connect.assert_called_once()


@pytest.mark.asyncio
async def test_exporter_metrics_update_error_handling(
    mock_devices, mock_influx_client
):
    """Test error handling during metrics update."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(side_effect=Exception("Info failed"))
    exporter.add_device(mock_device)
    
    await exporter.update_metrics()
    mock_device.get_device_info.assert_called_once()


@pytest.mark.asyncio
async def test_exporter_device_operation_error_handling(
    mock_devices, mock_influx_client
):
    """Test error handling during device operations."""
    exporter = TapoExporter(devices=mock_devices)
    mock_device = MagicMock()
    mock_device.name = "test_device"
    mock_device.device = MagicMock()
    mock_device.get_device_info = AsyncMock(return_value={"device_id": "test"})
    mock_device.get_current_power = AsyncMock(
        side_effect=Exception("Power failed")
    )
    exporter.add_device(mock_device)
    
    await exporter.update_metrics()
    mock_device.get_current_power.assert_called_once() 