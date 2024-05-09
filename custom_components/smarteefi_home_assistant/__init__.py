from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import SmarteefiDataUpdateCoordinator
from .smarteefy_cloud import SmarteefiAPI, SmarteefiAuthAPIResponse

PLATFORMS: list[Platform] = [
	Platform.SWITCH
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Set up Smarteefi from a config entry."""
	
	hass.data.setdefault(DOMAIN, {})
	api = SmarteefiAPI(hass)
	coordinator = SmarteefiDataUpdateCoordinator(hass=hass, api=api)
	hass.data[DOMAIN].setdefault("coordinator", {})
	hass.data[DOMAIN]["coordinator"][entry.entry_id] = coordinator
	await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
	
	return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
	"""Unload a config entry."""
	if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
		if "switch" in hass.data[DOMAIN] and entry.entry_id in hass.data[DOMAIN]["switch"]:
			hass.data[DOMAIN]["switch"].pop(
				entry.entry_id
			)
	
	return unload_ok
