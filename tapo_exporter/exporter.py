"""Exporter module for Tapo devices."""
import asyncio
import logging
import os
import traceback
import socket
from typing import List
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from prometheus_client import start_http_server

from .devices.p110 import P110Device
from .metrics import TapoMetrics

logger = logging.getLogger(__name__)

# US/Florida standard voltages
STANDARD_VOLTAGE_120V = 120
STANDARD_VOLTAGE_240V = 240

# Cost per kWh (Florida average rate)
COST_PER_KWH = float(os.getenv("COST_PER_KWH", "0.12"))  # Default to $0.12/kWh

class TapoExporter:
    def __init__(self, devices: List[P110Device] = None):
        self.devices = devices or []
        self.metrics = TapoMetrics()
        self.influx_client = InfluxDBClient(
            url=os.getenv("INFLUXDB_URL", "http://influxdb:8086"),
            token=os.getenv("INFLUXDB_TOKEN", "your-token-here"),
            org=os.getenv("INFLUXDB_ORG", "tapo")
        )
        self.write_api = self.influx_client.write_api(
            write_options=SYNCHRONOUS
        )
        # Store last power readings for energy calculation
        self.last_power_readings = {}
        self.last_update_time = {}
        self.accumulated_energy = {}  # Store accumulated energy for each device
        self.daily_cost = {}  # Store daily cost for each device
        
        # Initialize dictionaries for existing devices
        current_time = asyncio.get_event_loop().time()
        for device in self.devices:
            self.last_power_readings[device.name] = 0
            self.last_update_time[device.name] = current_time
            self.accumulated_energy[device.name] = 0.0
            self.daily_cost[device.name] = 0.0
            
        logger.info(
            f"Initialized TapoExporter with {len(self.devices)} devices, "
            f"cost per kWh: ${COST_PER_KWH:.2f}"
        )

    def add_device(self, device: P110Device) -> None:
        """Add a device to the exporter."""
        self.devices.append(device)
        self.metrics.device_count.inc()
        current_time = asyncio.get_event_loop().time()
        self.last_power_readings[device.name] = 0
        self.last_update_time[device.name] = current_time
        self.accumulated_energy[device.name] = 0.0
        self.daily_cost[device.name] = 0.0
        logger.info(f"Added device {device.name} to exporter")

    def calculate_cost(self, energy_wh: float) -> float:
        """Calculate cost from energy in watt-hours."""
        return (energy_wh / 1000) * COST_PER_KWH  # Convert to kWh and multiply by rate

    async def connect_devices(self) -> None:
        """Connect to all devices."""
        for device in self.devices:
            try:
                await device.connect()
            except Exception as e:
                logger.error(
                    f"Failed to connect to device {device.name}: {str(e)}"
                )

    async def update_metrics(self):
        """Update metrics for all devices."""
        current_time = asyncio.get_event_loop().time()
        
        for device in self.devices:
            device_name = device.name
            try:
                # Ensure device is initialized in our tracking dictionaries
                if device_name not in self.last_update_time:
                    self.last_power_readings[device_name] = 0
                    self.last_update_time[device_name] = current_time
                    self.accumulated_energy[device_name] = 0.0
                    self.daily_cost[device_name] = 0.0
                    logger.info(f"Initialized tracking for device {device_name}")

                if not device.device:
                    logger.warning(
                        f"Device {device_name} is not connected. "
                        "Skipping metrics update."
                    )
                    continue

                # Get device info
                try:
                    device_info = await device.get_device_info()
                    if not device_info:
                        logger.warning(
                            f"Failed to get device info for {device_name}. "
                            "Skipping metrics update."
                        )
                        continue
                    logger.info(
                        f"Device info for {device_name}: "
                        f"model={device_info.get('model', 'unknown')}, "
                        f"fw_ver={device_info.get('fw_ver', 'unknown')}, "
                        f"hw_ver={device_info.get('hw_ver', 'unknown')}, "
                        f"device_id={device_info.get('device_id', 'unknown')}, "
                        f"mac={device_info.get('mac', 'unknown')}, "
                        f"ip={device_info.get('ip', 'unknown')}, "
                        f"ssid={device_info.get('ssid', 'unknown')}, "
                        f"signal_level={device_info.get('signal_level', 0)}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error getting device info for {device_name}: {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    continue

                # Get current power
                try:
                    power_info = await device.get_current_power()
                    if not power_info:
                        logger.warning(
                            f"Failed to get power info for {device_name}. "
                            "Skipping metrics update."
                        )
                        continue
                    logger.info(
                        f"Power info for {device_name}: "
                        f"power={getattr(power_info, 'current_power', 0)}W, "
                        f"voltage={getattr(power_info, 'voltage', 0)}V, "
                        f"current={getattr(power_info, 'current', 0)}mA, "
                        f"power_factor={getattr(power_info, 'power_factor', 0)}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error getting power info for {device_name}: {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    continue

                # Get device usage
                try:
                    usage_info = await device.get_device_usage()
                    if not usage_info:
                        logger.warning(
                            f"Failed to get usage info for {device_name}. "
                            "Skipping metrics update."
                        )
                        continue
                    logger.info(
                        f"Usage info for {device_name}: "
                        f"today_energy={getattr(usage_info, 'today_energy', 0)}Wh, "
                        f"month_energy={getattr(usage_info, 'month_energy', 0)}Wh, "
                        f"today_runtime={getattr(usage_info, 'today_runtime', 0)}min, "
                        f"month_runtime={getattr(usage_info, 'month_runtime', 0)}min, "
                        f"power_saved={getattr(usage_info, 'power_saved', 0)}Wh, "
                        f"power_protection={getattr(usage_info, 'power_protection', False)}, "
                        f"overcurrent_protection={getattr(usage_info, 'overcurrent_protection', False)}, "
                        f"overheat_protection={getattr(usage_info, 'overheat_protection', False)}, "
                        f"signal_strength={getattr(usage_info, 'signal_strength', 0)}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error getting usage info for {device_name}: {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    continue

                # Update metrics
                try:
                    await self.metrics.update_metrics(device)
                except Exception as e:
                    logger.error(
                        f"Error updating metrics for {device_name}: {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    continue

                # Calculate current based on power and voltage
                voltage = int(getattr(power_info, "voltage", 0))
                power = int(getattr(power_info, "current_power", 0))
                current_ma = int(getattr(power_info, "current", 0))
                power_factor = float(getattr(power_info, "power_factor", 0))
                
                # If voltage is 0, determine appropriate voltage based on power
                if voltage == 0:
                    # Assume 240V for high-power devices (typically over 1800W)
                    voltage = (STANDARD_VOLTAGE_240V 
                             if power > 1800 
                             else STANDARD_VOLTAGE_120V)
                    logger.info(
                        f"Using default voltage for {device_name}: {voltage}V "
                        f"(power={power}W)"
                    )
                
                current = power / voltage if voltage > 0 else 0
                logger.info(
                    f"Calculated current for {device_name}: {current:.2f}A "
                    f"(power={power}W, voltage={voltage}V)"
                )

                # Calculate energy since last update
                time_diff = current_time - self.last_update_time[device_name]
                avg_power = (power + self.last_power_readings[device_name]) / 2
                energy_increment = (avg_power * time_diff) / 3600  # Convert to watt-hours
                
                # Update accumulated energy
                self.accumulated_energy[device_name] += energy_increment
                
                # Calculate cost
                cost_increment = self.calculate_cost(energy_increment)
                self.daily_cost[device_name] += cost_increment
                
                logger.info(
                    f"Energy calculation for {device_name}: "
                    f"time_diff={time_diff:.2f}s, "
                    f"avg_power={avg_power:.2f}W, "
                    f"energy_increment={energy_increment:.4f}Wh, "
                    f"total_accumulated={self.accumulated_energy[device_name]:.4f}Wh, "
                    f"cost_increment=${cost_increment:.4f}, "
                    f"total_cost=${self.daily_cost[device_name]:.4f}"
                )
                
                # Update stored values
                self.last_power_readings[device_name] = power
                self.last_update_time[device_name] = current_time

                # Get usage info
                today_energy = int(getattr(usage_info, "today_energy", 0))
                month_energy = int(getattr(usage_info, "month_energy", 0))
                today_runtime = int(getattr(usage_info, "today_runtime", 0))
                month_runtime = int(getattr(usage_info, "month_runtime", 0))
                power_saved = int(getattr(usage_info, "power_saved", 0))
                power_protection = bool(getattr(usage_info, "power_protection", False))
                overcurrent_protection = bool(getattr(usage_info, "overcurrent_protection", False))
                overheat_protection = bool(getattr(usage_info, "overheat_protection", False))
                signal_strength = int(getattr(usage_info, "signal_strength", 0))

                # Use accumulated energy if device reports 0
                if today_energy == 0:
                    today_energy = int(self.accumulated_energy[device_name])
                if month_energy == 0:
                    month_energy = int(self.accumulated_energy[device_name])

                # Calculate costs
                today_cost = self.calculate_cost(today_energy)
                month_cost = self.calculate_cost(month_energy)

                logger.info(
                    f"Final energy values for {device_name}: "
                    f"today_energy={today_energy}Wh, "
                    f"month_energy={month_energy}Wh, "
                    f"today_runtime={today_runtime}min, "
                    f"month_runtime={month_runtime}min, "
                    f"power_saved={power_saved}Wh, "
                    f"accumulated={self.accumulated_energy[device_name]:.4f}Wh, "
                    f"today_cost=${today_cost:.4f}, "
                    f"month_cost=${month_cost:.4f}"
                )

                # Write metrics to InfluxDB
                try:
                    from influxdb_client import Point
                    
                    point = Point("tapo_metrics") \
                        .tag("device_name", device_name) \
                        .tag("device_type", device_info.get("model", "unknown").lower()) \
                        .tag("fw_version", device_info.get("fw_ver", "unknown")) \
                        .tag("hw_version", device_info.get("hw_ver", "unknown")) \
                        .tag("device_id", device_info.get("device_id", "unknown")) \
                        .tag("mac", device_info.get("mac", "unknown")) \
                        .tag("ip", device_info.get("ip", "unknown")) \
                        .tag("ssid", device_info.get("ssid", "unknown")) \
                        .field("power_watts", power) \
                        .field("voltage_volts", voltage) \
                        .field("current_amps", current) \
                        .field("current_milliamps", current_ma) \
                        .field("power_factor", power_factor) \
                        .field("today_energy_wh", today_energy) \
                        .field("month_energy_wh", month_energy) \
                        .field("today_runtime_minutes", today_runtime) \
                        .field("month_runtime_minutes", month_runtime) \
                        .field("power_saved_wh", power_saved) \
                        .field("accumulated_energy_wh", self.accumulated_energy[device_name]) \
                        .field("power_protection", int(power_protection)) \
                        .field("overcurrent_protection", int(overcurrent_protection)) \
                        .field("overheat_protection", int(overheat_protection)) \
                        .field("signal_strength", signal_strength) \
                        .field("signal_level", int(device_info.get("signal_level", 0))) \
                        .field("today_cost_usd", today_cost) \
                        .field("month_cost_usd", month_cost) \
                        .field("accumulated_cost_usd", self.daily_cost[device_name])

                    self.write_api.write(bucket="tapo", record=point)
                    logger.info(
                        f"Wrote metrics to InfluxDB for device {device_name}: "
                        f"power={power}W, voltage={voltage}V, current={current:.2f}A, "
                        f"today_energy={today_energy}Wh, month_energy={month_energy}Wh, "
                        f"accumulated={self.accumulated_energy[device_name]:.4f}Wh, "
                        f"today_cost=${today_cost:.4f}, month_cost=${month_cost:.4f}"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to write metrics to InfluxDB for device {device_name}: "
                        f"{str(e)}\nTraceback: {traceback.format_exc()}"
                    )

            except Exception as e:
                logger.error(
                    f"Error updating metrics for device {device_name}: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                continue

    async def start(self, port: int = 9999):
        """Start the exporter."""
        try:
            # Start Prometheus HTTP server
            start_http_server(port)
            logger.info(f"Started Prometheus HTTP server on port {port}")
        except OSError as e:
            if e.errno == 48:  # Address already in use
                logger.warning(
                    f"Port {port} is already in use. "
                    "Prometheus metrics may not be available."
                )
                # Try to start server on a different port
                try:
                    start_http_server(0)  # Let the OS choose an available port
                    logger.info("Started Prometheus HTTP server on a different port")
                except Exception as e:
                    logger.error(f"Failed to start Prometheus server: {str(e)}")
                    raise  # Re-raise the exception to ensure the error is propagated
            else:
                raise
        
        # Connect to all devices
        await self.connect_devices()
        
        # Start metrics update loop
        while True:
            try:
                await self.update_metrics()
                # Update every 2 seconds to match main loop
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                logger.info("Metrics update loop cancelled")
                raise
            except Exception as e:
                msg = f"Error in metrics update loop: {str(e)}"
                logger.error(msg)
                await asyncio.sleep(5)  # Wait before retrying

    async def stop(self):
        """Stop the exporter."""
        # Close InfluxDB client
        self.influx_client.close()
        logger.info("Closed InfluxDB client") 