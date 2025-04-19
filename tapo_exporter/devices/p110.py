"""
P110/P115 device implementation.

This class supports both P110 and P115 devices as they share the same API
interface.
"""
from tapo import ApiClient
import logging

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

    async def connect(self):
        """Connect to the device"""
        try:
            logger.info(f"Attempting to connect to device {self.name} at {self.ip}")
            self.client = ApiClient(self.email, self.password)
            self.device = await self.client.p110(self.ip)
            logger.info(f"Successfully connected to device {self.name}")
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