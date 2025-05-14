import logging
from typing import Optional

from prometheus_client import CollectorRegistry, Gauge

from .devices.p110 import P110Device

logger = logging.getLogger(__name__)


class TapoMetrics:
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize TapoMetrics with an optional registry."""
        if registry is None:
            registry = CollectorRegistry()

        # Device metrics
        self.device_count = Gauge(
            "tapo_device_count",
            "Number of Tapo devices being monitored",
            registry=registry,
        )

        # Power metrics
        self.power_watts = Gauge(
            "tapo_power_watts",
            "Current power consumption in watts",
            ["device_name", "device_type"],
            registry=registry,
        )
        self.voltage_volts = Gauge(
            "tapo_voltage_volts",
            "Current voltage in volts",
            ["device_name", "device_type"],
            registry=registry,
        )
        self.current_amps = Gauge(
            "tapo_current_amps",
            "Reported current in amperes",
            ["device_name", "device_type"],
            registry=registry,
        )
        self.calculated_current_amps = Gauge(
            "tapo_calculated_current_amps",
            "Calculated current in amperes (power/voltage)",
            ["device_name", "device_type"],
            registry=registry,
        )

        # Energy metrics
        self.today_energy_wh = Gauge(
            "tapo_today_energy_wh",
            "Energy consumed today in watt-hours",
            ["device_name", "device_type"],
            registry=registry,
        )
        self.month_energy_wh = Gauge(
            "tapo_month_energy_wh",
            "Energy consumed this month in watt-hours",
            ["device_name", "device_type"],
            registry=registry,
        )
        self.power_saved_wh = Gauge(
            "tapo_power_saved_wh",
            "Power saved in watt-hours",
            ["device_name", "device_type"],
            registry=registry,
        )

        # Runtime metrics
        self.today_runtime_minutes = Gauge(
            "tapo_today_runtime_minutes",
            "Runtime today in minutes",
            ["device_name", "device_type"],
            registry=registry,
        )
        self.month_runtime_minutes = Gauge(
            "tapo_month_runtime_minutes",
            "Runtime this month in minutes",
            ["device_name", "device_type"],
            registry=registry,
        )

        # Protection status
        self.power_protection_status = Gauge(
            "tapo_power_protection_status",
            "Power protection status (1=enabled, 0=disabled)",
            ["device_name", "device_type"],
            registry=registry,
        )
        self.overcurrent_status = Gauge(
            "tapo_overcurrent_status",
            "Overcurrent protection status (1=enabled, 0=disabled)",
            ["device_name", "device_type"],
            registry=registry,
        )
        self.overheat_status = Gauge(
            "tapo_overheat_status",
            "Overheat protection status (1=enabled, 0=disabled)",
            ["device_name", "device_type"],
            registry=registry,
        )

        # Signal metrics
        self.signal_rssi = Gauge(
            "tapo_signal_rssi",
            "WiFi signal strength in dBm",
            ["device_name", "device_type"],
            registry=registry,
        )

    async def update_metrics(
        self, device: P110Device, update_usage: bool = True
    ) -> None:
        """Update all metrics for a device"""
        try:
            # Get device info
            device_info = await device.get_device_info()
            if device_info is None:
                logger.warning(
                    f"Failed to get device info for {device.name}. "
                    f"Skipping metrics update."
                )
                return

            device_name = (
                device_info.nickname
                if hasattr(device_info, "nickname")
                else device.name
            )
            device_type = (
                device_info.model.lower() if hasattr(device_info, "model") else "p110"
            )

            # Get power info
            power_info = await device.get_current_power()
            if power_info is None:
                logger.warning(
                    f"Failed to get power info for {device_name}. "
                    f"Skipping metrics update."
                )
                return

            # Extract power and voltage values
            power = abs(
                power_info.current_power if hasattr(power_info, "current_power") else 0
            )
            voltage = abs(power_info.voltage if hasattr(power_info, "voltage") else 0)
            reported_current = abs(
                power_info.current if hasattr(power_info, "current") else 0
            )

            # Only log power info if it's non-zero
            if power > 0:
                logger.info(f"Power consumption for {device_name}: {power} W")

            # Calculate current based on power and voltage
            if voltage > 0:
                calculated_current = power / voltage
                logger.info(
                    f"Calculated current for {device_name}: {calculated_current:.2f} A "
                    f"(power: {power} W, voltage: {voltage} V)"
                )
            else:
                calculated_current = 0
                # Only log debug message if we have power but no voltage
                if power > 0:
                    logger.debug(
                        f"Device {device_name} does not support voltage monitoring "
                        f"(power: {power} W)"
                    )

            # Update power metrics
            self.power_watts.labels(device_name, device_type).set(power)
            self.voltage_volts.labels(device_name, device_type).set(voltage)
            self.current_amps.labels(device_name, device_type).set(reported_current)
            self.calculated_current_amps.labels(device_name, device_type).set(
                calculated_current
            )

            # Only update usage metrics if requested
            if update_usage:
                # Get usage info
                usage_info = await device.get_device_usage()
                if usage_info is None:
                    logger.warning(
                        f"Failed to get usage info for {device_name}. "
                        f"Skipping usage metrics update."
                    )
                else:
                    # Extract usage values
                    today_energy = abs(
                        usage_info.today_energy
                        if hasattr(usage_info, "today_energy")
                        else 0
                    )
                    month_energy = abs(
                        usage_info.month_energy
                        if hasattr(usage_info, "month_energy")
                        else 0
                    )
                    power_saved = abs(
                        usage_info.power_saved
                        if hasattr(usage_info, "power_saved")
                        else 0
                    )
                    today_runtime = abs(
                        usage_info.today_runtime
                        if hasattr(usage_info, "today_runtime")
                        else 0
                    )
                    month_runtime = abs(
                        usage_info.month_runtime
                        if hasattr(usage_info, "month_runtime")
                        else 0
                    )

                    # Log usage info if any values are non-zero
                    if any(
                        [
                            today_energy,
                            month_energy,
                            power_saved,
                            today_runtime,
                            month_runtime,
                        ]
                    ):
                        logger.info(
                            f"Usage info for {device_name}: "
                            f"Today: {today_energy} Wh ({today_runtime} min), "
                            f"Month: {month_energy} Wh ({month_runtime} min), "
                            f"Power saved: {power_saved} Wh"
                        )

                    # Update usage metrics
                    self.today_energy_wh.labels(device_name, device_type).set(
                        today_energy
                    )

                    self.month_energy_wh.labels(device_name, device_type).set(
                        month_energy
                    )

                    self.power_saved_wh.labels(device_name, device_type).set(
                        power_saved
                    )

                    self.today_runtime_minutes.labels(device_name, device_type).set(
                        today_runtime
                    )

                    self.month_runtime_minutes.labels(device_name, device_type).set(
                        month_runtime
                    )

                    # Update protection status
                    power_protection = int(
                        usage_info.power_protection
                        if hasattr(usage_info, "power_protection")
                        else False
                    )
                    self.power_protection_status.labels(device_name, device_type).set(
                        power_protection
                    )

                    overcurrent = int(
                        usage_info.overcurrent_protection
                        if hasattr(usage_info, "overcurrent_protection")
                        else False
                    )
                    self.overcurrent_status.labels(device_name, device_type).set(
                        overcurrent
                    )

                    overheat = int(
                        usage_info.overheat_protection
                        if hasattr(usage_info, "overheat_protection")
                        else False
                    )
                    self.overheat_status.labels(device_name, device_type).set(overheat)

                    # Update signal info
                    signal = (
                        usage_info.signal_strength
                        if hasattr(usage_info, "signal_strength")
                        else 0
                    )
                    self.signal_rssi.labels(device_name, device_type).set(signal)

        except Exception as e:
            # Log the error with device IP if available, otherwise use name
            device_identifier = device.ip if hasattr(device, "ip") else device.name
            logger.error(
                f"Error updating metrics for device {device_identifier}: {str(e)}"
            )
