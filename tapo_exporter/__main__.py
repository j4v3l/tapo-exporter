import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import List
from dotenv import load_dotenv
from prometheus_client import start_http_server
from .devices.p110 import P110Device
from .exporter import TapoExporter

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s | %(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
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
logger.debug(f"TAPO_DEVICE_1_PASSWORD: {'*' * len(os.getenv('TAPO_DEVICE_1_PASSWORD', '')) if os.getenv('TAPO_DEVICE_1_PASSWORD') else None}")
logger.debug(f"TAPO_DEVICE_1_TYPE: {os.getenv('TAPO_DEVICE_1_TYPE')}")

def get_devices_from_env() -> List[P110Device]:
    """Get Tapo devices from environment variables"""
    devices = []
    device_count = int(os.getenv("TAPO_DEVICE_COUNT", "0"))
    logger.debug(f"Device count from env: {device_count}")
    
    # Get all environment variables
    env_vars = dict(os.environ)
    logger.debug("All environment variables:")
    for key, value in env_vars.items():
        if key.startswith("TAPO_DEVICE_"):
            logger.debug(f"{key}: {value}")
    
    for i in range(1, device_count + 1):
        # Use dict.get() instead of os.getenv()
        name = env_vars.get(f"TAPO_DEVICE_{i}_NAME")
        ip = env_vars.get(f"TAPO_DEVICE_{i}_IP")
        email = env_vars.get(f"TAPO_DEVICE_{i}_EMAIL")
        password = env_vars.get(f"TAPO_DEVICE_{i}_PASSWORD")
        device_type = env_vars.get(f"TAPO_DEVICE_{i}_TYPE", "p110").lower()
        
        logger.debug(f"Device {i} configuration:")
        logger.debug(f"  Name: {name}")
        logger.debug(f"  IP: {ip}")
        logger.debug(f"  Email: {email}")
        logger.debug(f"  Password: {'*' * len(password) if password else None}")
        logger.debug(f"  Type: {device_type}")
        
        if all([name, ip, email, password]):
            if device_type in ["p110", "p115"]:
                devices.append(P110Device(name, ip, email, password))
                logger.info(
                    f"Added {device_type.upper()} device {name} at {ip}"
                )
            else:
                logger.warning(
                    f"Invalid device type {device_type} for device {i}. "
                    "Using P110 as default."
                )
                devices.append(P110Device(name, ip, email, password))
        else:
            logger.warning(
                f"Missing configuration for device {i}. "
                "Skipping this device."
            )
            logger.debug("Missing values:")
            if not name:
                logger.debug("  - Name")
            if not ip:
                logger.debug("  - IP")
            if not email:
                logger.debug("  - Email")
            if not password:
                logger.debug("  - Password")
    
    return devices

async def main():
    """Main entry point for the Tapo exporter"""
    try:
        # Start Prometheus HTTP server
        port = int(os.getenv("PROMETHEUS_PORT", "8000"))
        start_http_server(port)
        logger.info(f"Started Prometheus metrics server on port {port}")
        
        devices = get_devices_from_env()
        if not devices:
            logger.error("No devices configured. Exiting.")
            return
        
        exporter = TapoExporter(devices)
        
        # Connect to all devices before starting the metrics collection
        try:
            await exporter.connect_devices()
            logger.info("Successfully connected to all devices")
        except Exception as e:
            logger.error(f"Failed to connect to devices: {str(e)}")
            return
        
        # Update metrics every 2 seconds
        while True:
            try:
                await exporter.update_metrics()
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(2)  # Wait before retrying
    except KeyboardInterrupt:
        logger.info("Exiting gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 