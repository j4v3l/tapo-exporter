"""Main entry point for the Tapo exporter."""

import asyncio
import logging
import os
import signal
from typing import List, Optional
from dotenv import load_dotenv
from prometheus_client import start_http_server
from .devices.p110 import P110Device
from .exporter import TapoExporter

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format="%(asctime)s | %(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Load environment variables
logger.debug("Loading environment variables...")
load_dotenv()
logger.debug("Environment variables loaded")

# Debug print all relevant environment variables
logger.debug("Environment variables:")
logger.debug(f"TAPO_DEVICE_COUNT: {os.getenv('TAPO_DEVICE_COUNT')}")
logger.debug(f"TAPO_DEVICE_1_NAME: {os.getenv('TAPO_DEVICE_1_NAME')}")
logger.debug(f"TAPO_DEVICE_1_IP: {os.getenv('TAPO_DEVICE_1_IP')}")
logger.debug(f"TAPO_DEVICE_1_EMAIL: {os.getenv('TAPO_DEVICE_1_EMAIL')}")
password = os.getenv("TAPO_DEVICE_1_PASSWORD", "")
password_len = len(password)
password_mask = "*" * password_len if password else ""
logger.debug(f"TAPO_DEVICE_1_PASSWORD: {password_mask}")
logger.debug(f"TAPO_DEVICE_1_TYPE: {os.getenv('TAPO_DEVICE_1_TYPE')}")


def get_devices_from_env() -> List[P110Device]:
    """Get Tapo devices from environment variables."""
    devices = []

    # Try new format first
    username = os.getenv("TAPO_USERNAME")
    password = os.getenv("TAPO_PASSWORD")
    device_ips = os.getenv("TAPO_DEVICES")

    if username and password and device_ips:
        logger.debug("Using new environment variable format")
        for ip in device_ips.split(","):
            ip = ip.strip()
            name = f"tapo_{ip.replace('.', '_')}"
            devices.append(
                P110Device(name=name, ip=ip, email=username, password=password)
            )
            logger.info(f"Added P110 device at {ip}")
        return devices

    # Fall back to old format
    logger.debug("Using old environment variable format")
    device_count_str = os.getenv("TAPO_DEVICE_COUNT", "0")
    try:
        device_count = int(device_count_str)
    except ValueError:
        logger.error(f"Invalid TAPO_DEVICE_COUNT value: {device_count_str}")
        return devices

    logger.debug(f"Device count from env: {device_count}")

    for i in range(1, device_count + 1):
        name_env = os.getenv(f"TAPO_DEVICE_{i}_NAME")
        ip_env = os.getenv(f"TAPO_DEVICE_{i}_IP")
        email_env = os.getenv(f"TAPO_DEVICE_{i}_EMAIL")
        password_env = os.getenv(f"TAPO_DEVICE_{i}_PASSWORD")
        device_type = os.getenv(f"TAPO_DEVICE_{i}_TYPE", "p110").lower()

        logger.debug(f"Device {i} configuration:")
        logger.debug(f"  Name: {name_env}")
        logger.debug(f"  IP: {ip_env}")
        logger.debug(f"  Email: {email_env}")
        password_mask = "*" * len(password_env) if password_env else ""
        logger.debug(f"  Password: {password_mask}")
        logger.debug(f"  Type: {device_type}")

        if name_env and ip_env and email_env and password_env:
            name = name_env
            ip = ip_env
            email = email_env
            password = password_env

            if device_type in ["p110", "p115"]:
                devices.append(
                    P110Device(name=name, ip=ip, email=email, password=password)
                )
                logger.info(f"Added {device_type.upper()} device {name} at {ip}")
            else:
                logger.warning(
                    f"Invalid device type {device_type} for device {i}. "
                    "Using P110 as default."
                )
                devices.append(
                    P110Device(name=name, ip=ip, email=email, password=password)
                )
        else:
            logger.warning(
                f"Missing configuration for device {i}. " "Skipping this device."
            )
            logger.debug("Missing values:")
            if not name_env:
                logger.debug("  - Name")
            if not ip_env:
                logger.debug("  - IP")
            if not email_env:
                logger.debug("  - Email")
            if not password_env:
                logger.debug("  - Password")

    return devices


async def main() -> None:
    """Main entry point for the Tapo exporter."""
    exporter: Optional[TapoExporter] = None
    try:
        # Start Prometheus HTTP server
        port_str = os.getenv("PROMETHEUS_PORT", "8000")
        try:
            port = int(port_str)
        except ValueError:
            logger.error(f"Invalid PROMETHEUS_PORT value: {port_str}")
            return

        start_http_server(port)
        logger.info(f"Started Prometheus metrics server on port {port}")

        devices = get_devices_from_env()
        if not devices:
            logger.error("No devices configured. Exiting.")
            return

        exporter = TapoExporter(devices)

        # Set up signal handlers
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(
            signal.SIGINT, lambda: asyncio.create_task(exporter.stop())
        )
        loop.add_signal_handler(
            signal.SIGTERM, lambda: asyncio.create_task(exporter.stop())
        )

        # Connect to all devices before starting the metrics collection
        try:
            await exporter.connect_devices()
            logger.info("Successfully connected to all devices")
        except Exception as e:
            logger.error(f"Failed to connect to devices: {str(e)}")
            return

        # Update metrics every 2 seconds
        await exporter.update_metrics()

        # Note: asyncio.sleep is mocked in tests to raise either
        # KeyboardInterrupt or CancelledError
        while True:
            try:
                # In test_main_keyboard_interrupt this raises KeyboardInterrupt
                # In test_main_loop_error this first returns None, then raises
                # CancelledError
                await asyncio.sleep(2)

                # In test_main_loop_error, this first raises Exception,
                # then CancelledError (never reaching the second call)
                await exporter.update_metrics()
            except KeyboardInterrupt:
                # This is needed for test_main_keyboard_interrupt
                logger.info("Keyboard interrupt received. Exiting gracefully...")
                # Stop the exporter before exiting
                if exporter:
                    await exporter.stop()
                # Don't re-raise, just return to exit gracefully
                return
            except asyncio.CancelledError:
                logger.info("Cancellation received. Exiting gracefully...")
                # Stop the exporter before re-raising
                if exporter:
                    await exporter.stop()
                # Re-raise CancelledError directly to the test
                raise
            except Exception as e:
                # Log non-cancellation errors
                logger.error(f"Error in main loop: {str(e)}")
                # Then continue the loop
    except KeyboardInterrupt:
        # This is needed for test_main_keyboard_interrupt
        logger.info("Exiting gracefully due to keyboard interrupt...")
        if exporter:
            await exporter.stop()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        # Ensure we stop the exporter on any fatal error
        if exporter:
            await exporter.stop()
        # Re-raise the exception for test_main_cleanup_on_error
        raise


if __name__ == "__main__":
    asyncio.run(main())
