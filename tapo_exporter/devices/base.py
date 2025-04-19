from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from tapo import ApiClient
import logging

logger = logging.getLogger(__name__)

class BaseTapoDevice(ABC):
    def __init__(self, name: str, ip: str, email: str, password: str):
        self.name = name
        self.ip = ip
        self.email = email
        self.password = password
        self.client: Optional[ApiClient] = None
        self.device = None
        logger.info(f"Initialized {self.__class__.__name__}: {name} at {ip}")

    async def connect(self) -> None:
        """Connect to the Tapo device"""
        try:
            logger.info(f"Attempting to connect to device {self.name} at {self.ip}")
            self.client = ApiClient(self.email, self.password)
            self.device = await self._get_device()
            logger.info(f"Successfully connected to device {self.name}")
        except Exception as e:
            logger.error(f"Failed to connect to device {self.name}: {str(e)}")
            raise

    @abstractmethod
    async def _get_device(self):
        """Get the specific device instance"""
        pass

    @abstractmethod
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        pass

    @abstractmethod
    async def get_current_power(self) -> Dict[str, Any]:
        """Get current power consumption"""
        pass

    @abstractmethod
    async def get_device_usage(self) -> Dict[str, Any]:
        """Get device usage statistics"""
        pass

    async def turn_on(self) -> None:
        """Turn the device on"""
        if self.device:
            await self.device.on()

    async def turn_off(self) -> None:
        """Turn the device off"""
        if self.device:
            await self.device.off()

    @property
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.device is not None 