"""
P110/P115 device implementation.

This class supports both P110 and P115 devices as they share the same API
interface.
"""

import glob
import logging
import os
import time
from typing import Any, Dict, Optional, cast
from tapo import ApiClient

logger = logging.getLogger(__name__)


class P110Device:
    def __init__(self, name: str, ip: str, email: str, password: str):
        self.name = name
        self.ip = ip
        self.email = email
        self.password = password
        self.client: Optional[ApiClient] = None
        self.device: Any = None
        logger.info(f"Initialized P110Device: {name} at {ip}")

    def _clean_credentials(self) -> None:
        """Clean up any cached credentials"""
        # Remove any cached credentials from /tmp
        tmp_files = glob.glob("/tmp/tapo_*")
        for f in tmp_files:
            try:
                os.remove(f)
                logger.debug(f"Removed cached credential file: {f}")
            except Exception as e:
                logger.warning(f"Failed to remove {f}: {str(e)}")

        # Remove any Tapo-related JSON files in the current directory
        json_files = glob.glob("tapo_*.json")
        for f in json_files:
            try:
                os.remove(f)
                logger.debug(f"Removed cached credential file: {f}")
            except Exception as e:
                logger.warning(f"Failed to remove {f}: {str(e)}")

    async def connect(self) -> None:
        """Connect to the device"""
        try:
            logger.info(f"Attempting to connect to device {self.name} at {self.ip}")

            # Clean up any cached credentials before attempting to connect
            self._clean_credentials()

            # Initialize the client with debug logging
            logger.debug("Initializing ApiClient with credentials")
            self.client = ApiClient(self.email, self.password)

            # Try to connect with the specified device type
            device_type = os.getenv("TAPO_DEVICE_1_TYPE", "p115").lower()
            logger.info(f"Using device type: {device_type}")

            # Add a small delay between attempts
            time.sleep(1)

            try:
                if device_type == "p115":
                    logger.debug("Attempting to connect as P115 device")
                    if self.client:  # Check to ensure client is not None
                        self.device = await self.client.p115(self.ip)
                else:
                    logger.debug("Attempting to connect as P110 device")
                    if self.client:  # Check to ensure client is not None
                        self.device = await self.client.p110(self.ip)

                # Verify the connection by getting device info
                logger.debug("Attempting to get device info")
                if self.device:  # Check to ensure device is not None
                    device_info = await self.device.get_device_info()
                    logger.info(f"Successfully connected to device {self.name}")
                    logger.info(f"Device model: {device_info.model}")
                    logger.info(f"Device firmware: {device_info.fw_ver}")

            except Exception as e:
                logger.error(f"Failed to connect using {device_type}: {str(e)}")
                # Add a delay before trying the alternative type
                time.sleep(2)

                # Try the alternative device type
                alternative_type = "p110" if device_type == "p115" else "p115"
                logger.info(f"Trying alternative device type: {alternative_type}")

                if alternative_type == "p115" and self.client:
                    self.device = await self.client.p115(self.ip)
                elif self.client:
                    self.device = await self.client.p110(self.ip)

                # Verify the connection
                logger.debug("Attempting to get device info with alternative type")
                if self.device:  # Check to ensure device is not None
                    device_info = await self.device.get_device_info()
                    alt_msg = f"Successfully connected using alternative type {alternative_type}"
                    logger.info(alt_msg)
                    logger.info(f"Device model: {device_info.model}")
                    logger.info(f"Device firmware: {device_info.fw_ver}")

        except Exception as e:
            logger.error(f"Failed to connect to device {self.name}: {str(e)}")
            raise

    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        if not self.device:
            raise RuntimeError("Device not connected")
        result = await self.device.get_device_info_json()
        return cast(Dict[str, Any], result)

    async def get_current_power(self) -> Dict[str, Any]:
        """Get current power consumption"""
        if not self.device:
            raise RuntimeError("Device not connected")
        result = await self.device.get_current_power()
        return cast(Dict[str, Any], result)

    async def get_device_usage(self) -> Dict[str, Any]:
        """Get device usage statistics"""
        if not self.device:
            raise RuntimeError("Device not connected")
        result = await self.device.get_device_usage()
        return cast(Dict[str, Any], result)
