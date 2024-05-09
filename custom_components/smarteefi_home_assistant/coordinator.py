"""Data update coordinator for the Smarteefi integration."""

from logging import getLogger

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import MANUFACTURER, DOMAIN
from .smarteefy_cloud import SmarteefiAPI

_LOGGER = getLogger(__name__)


class SmarteefiDataUpdateCoordinator(DataUpdateCoordinator):
	"""Smarteefi data update coordinator."""
	
	def __init__(
			self, hass: HomeAssistant, api: SmarteefiAPI
	) -> None:
		"""Init data update coordinator."""
		self.api = api
		self.hass = hass
		super().__init__(hass, _LOGGER, name=f"{MANUFACTURER} Coordinator")
	
	def get_devices(self):
		"""Get list of available devices."""
		self.hass.data[DOMAIN]["devices"] = self.api.getDevices()
		return self.hass.data[DOMAIN]["devices"]
