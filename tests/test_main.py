"""Tests for the main module."""
from unittest.mock import MagicMock, patch

import pytest

from tapo_exporter.__main__ import main


@pytest.mark.asyncio
async def test_main_initialization():
    """Test main initialization."""
    with patch("tapo_exporter.__main__.TapoExporter") as mock_exporter:
        await main()
        mock_exporter.assert_called_once()


@pytest.mark.asyncio
async def test_main_device_creation():
    """Test device creation in main."""
    with patch("tapo_exporter.__main__.P110Device") as mock_device:
        await main()
        mock_device.assert_called_once()


@pytest.mark.asyncio
async def test_main_exporter_start():
    """Test exporter start in main."""
    mock_exporter_instance = MagicMock()
    
    with patch(
        "tapo_exporter.__main__.TapoExporter",
        return_value=mock_exporter_instance
    ):
        await main()
        mock_exporter_instance.start.assert_called_once()


@pytest.mark.asyncio
async def test_main_signal_handling():
    """Test signal handling in main."""
    mock_exporter_instance = MagicMock()
    
    with patch(
        "tapo_exporter.__main__.TapoExporter",
        return_value=mock_exporter_instance
    ):
        with patch("tapo_exporter.__main__.asyncio") as mock_asyncio:
            await main()
            mock_asyncio.get_event_loop.assert_called_once()
            (
                mock_asyncio.get_event_loop.return_value
                .add_signal_handler.assert_called()
            ) 