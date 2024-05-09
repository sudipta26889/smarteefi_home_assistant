"""Device as wrapper for Smarteefi Cloud APIs."""
from logging import getLogger
from typing import Any

from homeassistant.core import HomeAssistant
from .smarteefy_cloud import SmarteefiAPI

_LOGGER = getLogger(__name__)


class SmarteefiDevice:
    """Smarteefi device."""

    def __init__(self, hass: HomeAssistant, data: dict[str, Any], api: SmarteefiAPI) -> None:
        """Init Smarteefi device."""
        self.devicename = data["devicename"]
        self.serial = data["serial"]
        self.group_id = data["group_id"]
        self.ip = data["ip"]
        self.port = data["port"]
        self.hass = hass
        self._api = api
