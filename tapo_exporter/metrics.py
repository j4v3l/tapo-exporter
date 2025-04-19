import logging
from prometheus_client import Gauge
from .devices.p110 import P110Device

logger = logging.getLogger(__name__)

class TapoMetrics:
    def __init__(self):
        # Device metrics
        self.device_count = Gauge(
            "tapo_device_count",
            "Number of Tapo devices being monitored",
        )
        
        # Power metrics
        self.power_watts = Gauge(
            "tapo_power_watts",
            "Current power consumption in watts",
            ["device_name", "device_type"],
        )
        self.voltage_volts = Gauge(
            "tapo_voltage_volts",
            "Current voltage in volts",
            ["device_name", "device_type"],
        )
        self.current_amps = Gauge(
            "tapo_current_amps",
            "Reported current in amperes",
            ["device_name", "device_type"],
        )
        self.calculated_current_amps = Gauge(
            "tapo_calculated_current_amps",
            "Calculated current in amperes (power/voltage)",
            ["device_name", "device_type"],
        )
        
        # Energy metrics
        self.today_energy_wh = Gauge(
            "tapo_today_energy_wh",
            "Energy consumed today in watt-hours",
            ["device_name", "device_type"],
        )
        self.month_energy_wh = Gauge(
            "tapo_month_energy_wh",
            "Energy consumed this month in watt-hours",
            ["device_name", "device_type"],
        )
        self.power_saved_wh = Gauge(
            "tapo_power_saved_wh",
            "Power saved in watt-hours",
            ["device_name", "device_type"],
        )
        
        # Runtime metrics
        self.today_runtime_minutes = Gauge(
            "tapo_today_runtime_minutes",
            "Runtime today in minutes",
            ["device_name", "device_type"],
        )
        self.month_runtime_minutes = Gauge(
            "tapo_month_runtime_minutes",
            "Runtime this month in minutes",
            ["device_name", "device_type"],
        )
        
        # Protection status
        self.power_protection_status = Gauge(
            "tapo_power_protection_status",
            "Power protection status (1=enabled, 0=disabled)",
            ["device_name", "device_type"],
        )
        self.overcurrent_status = Gauge(
            "tapo_overcurrent_status",
            "Overcurrent protection status (1=enabled, 0=disabled)",
            ["device_name", "device_type"],
        )
        self.overheat_status = Gauge(
            "tapo_overheat_status",
            "Overheat protection status (1=enabled, 0=disabled)",
            ["device_name", "device_type"],
        )
        
        # Signal metrics
        self.signal_rssi = Gauge(
            "tapo_signal_rssi",
            "WiFi signal strength in dBm",
            ["device_name", "device_type"],
        )

    async def update_metrics(self, device: P110Device, update_usage: bool = True) -> None:
        """Update all metrics for a device"""
        try:
            # Get device info
            device_info = await device.get_device_info()
            device_name = device_info.get("nickname", device.name)
            device_type = device_info.get("model", "p110").lower()
            
            # Get power info
            power_info = await device.get_current_power()
            logger.info(f"Raw power info for {device_name}: {power_info}")
            
            # Extract power and voltage values
            power = power_info.get("current_power", 0)
            voltage = power_info.get("voltage", 0)
            reported_current = power_info.get("current", 0)
            
            logger.info(
                f"Power: {power} W, Voltage: {voltage} V, "
                f"Reported Current: {reported_current} A for device {device_name}"
            )
            
            # Calculate current based on power and voltage
            if voltage > 0:
                calculated_current = power / voltage
                logger.info(
                    f"Calculated current for {device_name}: {calculated_current:.2f} A "
                    f"(power: {power} W, voltage: {voltage} V)"
                )
            else:
                calculated_current = 0
                logger.warning(
                    f"Invalid voltage ({voltage}V) for current calculation on {device_name}"
                )
            
            # Update power metrics
            self.power_watts.labels(device_name, device_type).set(power)
            self.voltage_volts.labels(device_name, device_type).set(voltage)
            self.current_amps.labels(device_name, device_type).set(reported_current)
            self.calculated_current_amps.labels(device_name, device_type).set(
                calculated_current
            )
            
            # Only update usage metrics every 30 seconds
            if update_usage:
                # Get usage info
                usage_info = await device.get_device_usage()
                logger.info(f"Raw usage info for {device_name}: {usage_info}")
                
                # Update usage metrics
                self.today_energy_wh.labels(device_name, device_type).set(
                    usage_info.get("today_energy", 0)
                )
                self.month_energy_wh.labels(device_name, device_type).set(
                    usage_info.get("month_energy", 0)
                )
                self.power_saved_wh.labels(device_name, device_type).set(
                    usage_info.get("power_saved", 0)
                )
                self.today_runtime_minutes.labels(device_name, device_type).set(
                    usage_info.get("today_runtime", 0)
                )
                self.month_runtime_minutes.labels(device_name, device_type).set(
                    usage_info.get("month_runtime", 0)
                )
                
                # Update protection status
                self.power_protection_status.labels(device_name, device_type).set(
                    int(usage_info.get("power_protection", False))
                )
                self.overcurrent_status.labels(device_name, device_type).set(
                    int(usage_info.get("overcurrent_protection", False))
                )
                self.overheat_status.labels(device_name, device_type).set(
                    int(usage_info.get("overheat_protection", False))
                )
                
                # Update signal info
                self.signal_rssi.labels(device_name, device_type).set(
                    usage_info.get("signal_strength", 0)
                )
            
        except Exception as e:
            logger.error(f"Error updating metrics for device {device.ip}: {str(e)}") 