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


@pytest.mark.asyncio
async def test_exporter_calculate_cost():
    """Test the calculate_cost method."""
    devices = [MagicMock()]
    exporter = TapoExporter(devices)
    
    # Test with 1000 Wh (1 kWh)
    cost = exporter.calculate_cost(1000)
    assert cost == 0.12  # COST_PER_KWH is 0.12 in the code
    
    # Test with 500 Wh (0.5 kWh)
    cost = exporter.calculate_cost(500)
    assert cost == 0.06
    
    # Test with 0 Wh
    cost = exporter.calculate_cost(0)
    assert cost == 0


@pytest.mark.asyncio
async def test_exporter_zero_voltage_handling():
    """Test handling of zero voltage in update_metrics."""
    # Set up a mock device
    device = MagicMock()
    device.name = "test_device"
    device.device = True  # Connected
    
    # Set up power info with zero voltage
    power_info = MagicMock()
    power_info.voltage = 0
    power_info.current_power = 2000  # High power for 240V test
    power_info.current = 10000  # 10A in milliamps
    power_info.power_factor = 0.9
    
    # Set up normal device and usage info
    device_info = {"model": "P110", "hw_ver": "1.0"}
    usage_info = MagicMock()
    usage_info.today_energy = 1000
    usage_info.month_energy = 30000
    
    # Mock the device methods as async
    device.get_device_info = AsyncMock(return_value=device_info)
    device.get_current_power = AsyncMock(return_value=power_info)
    device.get_device_usage = AsyncMock(return_value=usage_info)
    
    # Create exporter with the mock device
    exporter = TapoExporter([device])
    
    # Execute update_metrics
    await exporter.update_metrics()
    
    # Check if high-power device gets 240V by default
    assert exporter.last_power_readings[device.name] == 2000
    
    # Now test with low power (should default to 120V)
    power_info.current_power = 100  # Low power
    await exporter.update_metrics()


@pytest.mark.asyncio
async def test_exporter_init_tracking_during_update():
    """Test initialization of tracking dictionaries during update_metrics."""
    # Set up mock device
    device = MagicMock()
    device.name = "new_device"
    device.device = True
    
    # Set up normal device, power, and usage info
    device_info = {"model": "P110", "hw_ver": "1.0"}
    power_info = MagicMock()
    power_info.voltage = 120
    power_info.current_power = 100
    power_info.current = 1000
    power_info.power_factor = 0.9
    
    usage_info = MagicMock()
    usage_info.today_energy = 1000
    usage_info.month_energy = 30000
    
    # Mock the device methods
    device.get_device_info.return_value = device_info
    device.get_current_power.return_value = power_info
    device.get_device_usage.return_value = usage_info
    
    # Create exporter without devices
    exporter = TapoExporter([])
    
    # Add the device after initialization
    exporter.devices.append(device)
    
    # Execute update_metrics
    await exporter.update_metrics()
    
    # Check if tracking dictionaries were initialized
    assert device.name in exporter.last_update_time
    assert device.name in exporter.last_power_readings
    assert device.name in exporter.accumulated_energy
    assert device.name in exporter.daily_cost


@pytest.mark.asyncio
async def test_exporter_energy_calculation():
    """Test energy and cost calculation in update_metrics."""
    # Set up mock device
    device = MagicMock()
    device.name = "test_device"
    device.device = True
    
    # Set up normal device, power, and usage info
    device_info = {"model": "P110", "hw_ver": "1.0"}
    power_info = MagicMock()
    power_info.voltage = 120
    power_info.current_power = 100  # 100W
    power_info.current = 833  # ~833mA at 120V
    power_info.power_factor = 0.9
    
    usage_info = MagicMock()
    usage_info.today_energy = 1000
    usage_info.month_energy = 30000
    
    # Mock the device methods as async
    device.get_device_info = AsyncMock(return_value=device_info)
    device.get_current_power = AsyncMock(return_value=power_info)
    device.get_device_usage = AsyncMock(return_value=usage_info)
    
    # Create exporter with the mock device
    exporter = TapoExporter([device])
    
    # Initialize tracking for the device
    current_time = asyncio.get_event_loop().time()
    exporter.last_update_time[device.name] = current_time - 3600  # 1 hour ago
    exporter.last_power_readings[device.name] = 100  # Same power as current
    exporter.accumulated_energy[device.name] = 0
    exporter.daily_cost[device.name] = 0
    
    # Execute update_metrics
    await exporter.update_metrics()
    
    # Check energy calculation (100W for 1 hour = 100Wh)
    assert exporter.accumulated_energy[device.name] == pytest.approx(100, rel=0.1)
    
    # Check cost calculation (100Wh = 0.1kWh, at $0.12/kWh = $0.012)
    assert exporter.daily_cost[device.name] == pytest.approx(0.012, rel=0.1)


@pytest.mark.asyncio
async def test_exporter_start_and_stop():
    """Test the start and stop methods."""
    # Create a mock device with async methods
    device = MagicMock()
    device.name = "test_device"
    device.device = AsyncMock()
    device.get_device_info = AsyncMock(return_value={"model": "test"})
    device.get_current_power = AsyncMock(return_value=MagicMock(
        current_power=100,
        voltage=120,
        current=1000,
        power_factor=0.9
    ))
    device.get_device_usage = AsyncMock(return_value=MagicMock(
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
    
    # Create the exporter with mocked InfluxDB client
    with patch("influxdb_client.InfluxDBClient") as mock_influx, \
         patch("prometheus_client.start_http_server") as mock_start_server:
        mock_write_api = MagicMock()
        mock_influx.return_value.write_api = mock_write_api
        exporter = TapoExporter([device])
        
        # Mock connect_devices
        exporter.connect_devices = AsyncMock()
        
        # Start the exporter
        task = asyncio.create_task(exporter.start(port=9999))
        
        # Wait for server to start
        await asyncio.sleep(0.1)
        
        # Verify server was started
        mock_start_server.assert_called_once_with(9999)
        
        # Cancel the task after a short delay
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Stop the exporter
        await exporter.stop()
        
        # Verify tasks were cancelled if they exist
        if hasattr(exporter, "_tasks") and exporter._tasks:
            for task in exporter._tasks:
                assert task.cancelled() 