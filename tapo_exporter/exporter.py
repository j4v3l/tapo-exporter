import asyncio
import logging
import os
from typing import List
from prometheus_client import Gauge, Counter
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from .devices.p110 import P110Device

logger = logging.getLogger(__name__)

# Prometheus metrics
tapo_power = Gauge(
    'tapo_power_watts', 
    'Current power consumption in watts',
    ['device_name']
)
tapo_voltage = Gauge(
    'tapo_voltage_volts', 
    'Current voltage in volts',
    ['device_name']
)
tapo_current = Gauge(
    'tapo_current_amps', 
    'Current in amperes',
    ['device_name']
)
tapo_runtime = Counter(
    'tapo_runtime_seconds', 
    'Total device runtime in seconds',
    ['device_name']
)
tapo_signal_strength = Gauge(
    'tapo_signal_strength', 
    'WiFi signal strength level',
    ['device_name']
)
tapo_signal_rssi = Gauge(
    'tapo_signal_rssi', 
    'WiFi signal RSSI in dBm',
    ['device_name']
)
tapo_today_energy = Gauge(
    'tapo_today_energy_wh', 
    'Energy consumption today in watt-hours',
    ['device_name']
)
tapo_month_energy = Gauge(
    'tapo_month_energy_wh', 
    'Energy consumption this month in watt-hours',
    ['device_name']
)
tapo_today_runtime = Gauge(
    'tapo_today_runtime_minutes', 
    'Runtime today in minutes',
    ['device_name']
)
tapo_month_runtime = Gauge(
    'tapo_month_runtime_minutes', 
    'Runtime this month in minutes',
    ['device_name']
)
tapo_power_saved = Gauge(
    'tapo_power_saved_wh', 
    'Power saved in watt-hours',
    ['device_name']
)
tapo_device_status = Gauge(
    'tapo_device_status', 
    'Device status (1=normal, 0=abnormal)', 
    ['device_name', 'status_type']
)


class TapoExporter:
    def __init__(self, devices: List[P110Device]):
        self.devices = devices
        self.influx_client = InfluxDBClient(
            url=os.getenv("INFLUXDB_URL", "http://influxdb:8086"),
            token=os.getenv("INFLUXDB_TOKEN", "your-token-here"),
            org=os.getenv("INFLUXDB_ORG", "tapo")
        )
        self.write_api = self.influx_client.write_api(
            write_options=SYNCHRONOUS
        )
        logger.info(f"Initialized TapoExporter with {len(devices)} devices")

    async def connect_devices(self):
        """Ensure all devices are connected"""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for device in self.devices:
            retries = 0
            while retries < max_retries:
                try:
                    logger.info(
                        "Connecting to device {} at {} (attempt {}/{})".format(
                            device.name,
                            device.ip,
                            retries + 1,
                            max_retries
                        )
                    )
                    await device.connect()
                    logger.info(f"Successfully connected to device {device.name}")
                    break
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(
                            f"Failed to connect to device {device.name} after "
                            f"{max_retries} attempts: {str(e)}"
                        )
                        raise
                    logger.warning(
                        f"Connection attempt {retries} failed for device "
                        f"{device.name}: {str(e)}. Retrying in {retry_delay} seconds..."
                    )
                    await asyncio.sleep(retry_delay)

    async def update_metrics(self):
        """Update metrics for all devices"""
        for device in self.devices:
            try:
                # Ensure device is connected
                if not device.device:
                    logger.info(
                        "Device {} not connected, reconnecting...".format(
                            device.name
                        )
                    )
                    await device.connect()
                
                # Get device info
                info = await device.get_device_info()
                
                # Create InfluxDB point
                point = Point("tapo_metrics").tag("device_name", device.name)
                
                # Update device status metrics
                status_types = ['power_protection', 'overcurrent', 'overheat']
                for status_type in status_types:
                    status_key = f'{status_type}_status'
                    status_value = 1 if info[status_key] == 'normal' else 0
                    tapo_device_status.labels(
                        device_name=device.name,
                        status_type=status_type
                    ).set(status_value)
                    point.field(f"{status_type}_status", status_value)
                
                # Update signal metrics
                tapo_signal_strength.labels(
                    device_name=device.name
                ).set(info['signal_level'])
                point.field("signal_strength", info['signal_level'])
                
                tapo_signal_rssi.labels(
                    device_name=device.name
                ).set(info['rssi'])
                point.field("signal_rssi", info['rssi'])
                
                # Update runtime
                tapo_runtime.labels(
                    device_name=device.name
                )._value.set(info['on_time'])
                point.field("runtime_seconds", info['on_time'])
                
                # Get current power and energy data
                power_info = await device.get_current_power()
                power_dict = power_info.to_dict()
                
                # Calculate current based on power and voltage
                power = power_dict['current_power']
                voltage = power_dict.get('voltage', 120)
                logger.info(
                    f"Power: {power} W, Voltage: {voltage} V for device {device.name}"
                )
                
                if voltage == 0:
                    logger.warning(
                        f"Voltage is 0 for device {device.name}, "
                        "cannot calculate current"
                    )
                    current = 0
                else:
                    # Convert current to milliamps and then to integer
                    current = int((power / voltage) * 1000)
                    logger.info(
                        f"Calculated current for {device.name}: {current} mA "
                        f"(power: {power} W, voltage: {voltage} V)"
                    )
                
                # Update power metrics
                tapo_power.labels(
                    device_name=device.name
                ).set(power)
                point.field("power_watts", power)
                
                # Update voltage and current metrics
                tapo_voltage.labels(
                    device_name=device.name
                ).set(voltage)
                point.field("voltage_volts", voltage)
                
                tapo_current.labels(
                    device_name=device.name
                ).set(current)
                point.field("current_amps", current)
                
                # Get device usage
                usage = await device.get_device_usage()
                usage_dict = usage.to_dict()
                
                tapo_today_energy.labels(
                    device_name=device.name
                ).set(usage_dict['power_usage']['today'])
                point.field(
                    "today_energy_wh",
                    usage_dict['power_usage']['today']
                )
                
                tapo_month_energy.labels(
                    device_name=device.name
                ).set(usage_dict['power_usage']['past30'])
                point.field(
                    "month_energy_wh",
                    usage_dict['power_usage']['past30']
                )
                
                tapo_today_runtime.labels(
                    device_name=device.name
                ).set(usage_dict['time_usage']['today'])
                point.field(
                    "today_runtime_minutes",
                    usage_dict['time_usage']['today']
                )
                
                tapo_month_runtime.labels(
                    device_name=device.name
                ).set(usage_dict['time_usage']['past30'])
                point.field(
                    "month_runtime_minutes",
                    usage_dict['time_usage']['past30']
                )
                
                tapo_power_saved.labels(
                    device_name=device.name
                ).set(usage_dict['saved_power']['today'])
                point.field(
                    "power_saved_wh",
                    usage_dict['saved_power']['today']
                )
                
                # Write to InfluxDB
                self.write_api.write(
                    bucket=os.getenv("INFLUXDB_BUCKET", "tapo_metrics"),
                    org=os.getenv("INFLUXDB_ORG", "tapo"),
                    record=point
                )
                
                logger.debug(f"Updated metrics for device {device.name}")
            except Exception as e:
                logger.error(
                    "Error updating metrics for device "
                    f"{device.name}: {str(e)}"
                )
                # Reset device state on error
                device.device = None
                device.client = None

    async def run(self):
        """Main loop for the exporter"""
        # Initial connection to all devices
        await self.connect_devices()
        
        while True:
            try:
                await self.update_metrics()
                await asyncio.sleep(2)  # Update every 2 seconds
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(2)  # Wait before retrying 