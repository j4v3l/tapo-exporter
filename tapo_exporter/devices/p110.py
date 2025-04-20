"""
P110/P115 device implementation.

This class supports both P110 and P115 devices as they share the same API
interface.
"""
from tapo import ApiClient
import logging
import os
import glob
import time

logger = logging.getLogger(__name__)


class P110Device:
    def __init__(self, name: str, ip: str, email: str, password: str):
        self.name = name
        self.ip = ip
        self.email = email
        self.password = password
        self.client = None
        self.device = None
        logger.info(f"Initialized P110Device: {name} at {ip}")

    def _clean_credentials(self):
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

    async def connect(self):
        """Connect to the device"""
        try:
            logger.info(f"Attempting to connect to device {self.name} at {self.ip}")
            
            # Clean up any cached credentials before attempting to connect
            self._clean_credentials()
            
            # Initialize the client with debug logging
            logger.debug("Initializing ApiClient with credentials")
            self.client = ApiClient(self.email, self.password)
            
            # Try to connect with the specified device type
            device_type = os.getenv(f"TAPO_DEVICE_1_TYPE", "p115").lower()
            logger.info(f"Using device type: {device_type}")
            
            # Add a small delay between attempts
            time.sleep(1)
            
            try:
                if device_type == "p115":
                    logger.debug("Attempting to connect as P115 device")
                    self.device = await self.client.p115(self.ip)
                else:
                    logger.debug("Attempting to connect as P110 device")
                    self.device = await self.client.p110(self.ip)
                
                # Verify the connection by getting device info
                logger.debug("Attempting to get device info")
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
                
                if alternative_type == "p115":
                    self.device = await self.client.p115(self.ip)
                else:
                    self.device = await self.client.p110(self.ip)
                
                # Verify the connection
                logger.debug("Attempting to get device info with alternative type")
                device_info = await self.device.get_device_info()
                logger.info(f"Successfully connected using alternative type {alternative_type}")
                logger.info(f"Device model: {device_info.model}")
                logger.info(f"Device firmware: {device_info.fw_ver}")
                
        except Exception as e:
            logger.error(f"Failed to connect to device {self.name}: {str(e)}")
            raise

    async def get_device_info(self):
        """Get device information"""
        if not self.device:
            raise RuntimeError("Device not connected")
        return await self.device.get_device_info_json()

    async def get_current_power(self):
        """Get current power consumption"""
        if not self.device:
            raise RuntimeError("Device not connected")
        return await self.device.get_current_power()

    async def get_device_usage(self):
        """Get device usage statistics"""
        if not self.device:
            raise RuntimeError("Device not connected")
        return await self.device.get_device_usage() 