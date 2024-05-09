"""Base Smarteefi entity."""

from logging import Logger, getLogger
from typing import TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, MANUFACTURER
from .coordinator import SmarteefiDataUpdateCoordinator
from .device import SmarteefiDevice

_EntityT = TypeVar("_EntityT", bound="SmarteefiEntity")

_LOGGER = getLogger(__name__)


async def platform_async_setup_entry(
		hass: HomeAssistant,
		entry: ConfigEntry,
		async_add_entities: AddEntitiesCallback,
		entity_type: _EntityT,
) -> None:
	"""Set up an Smarteefi platform."""
	# print("entity platform_async_setup_entry called", hass.data[DOMAIN])
	coordinator = None
	if "access_token" in hass.data[DOMAIN]:
		coordinator: SmarteefiDataUpdateCoordinator = hass.data[DOMAIN]["coordinator"][entry.entry_id]
		await hass.async_add_executor_job(coordinator.get_devices)
	if "devices" in hass.data[DOMAIN] and "switches" in hass.data[DOMAIN]["devices"]:
		hass.data[DOMAIN].setdefault("switch", {})
		entities_to_add = []
		for each_switch in hass.data[DOMAIN]["devices"]['switches']:
			if each_switch['serial'] == entry.data['serial']:
				device_info = {
					"devicename": entry.data['devname'],
					"serial": entry.data['serial'],
					"group_id": each_switch['group_id'],
					"ip": entry.data['ip'],
					"port": entry.data.get('port', 10201),
					"state": entry.data['devname'],
				}
				cloud_statusmap = 0
				if coordinator:
					device_more_info = await hass.async_add_executor_job(coordinator.api.getDeviceMoreInfo,
					                                                     each_switch['serial'], each_switch['map'])
					if device_more_info.get('result', '') == "success":
						cloud_statusmap = device_more_info['statusmap']
					# print(" >> device_more_info >>", device_more_info)
				# Pre-fill devname and ip if available
				device = SmarteefiDevice(coordinator.hass, device_info, coordinator.api)
				entities_to_add.append(
					entity_type(coordinator=coordinator, device=device, map_id=each_switch['map'],
					            switchname=each_switch['name'], cloud_statusmap=cloud_statusmap)
				)
		async_add_entities(entities_to_add)


class SmarteefiEntity(CoordinatorEntity, Entity):
	"""Smarteefi base entity."""
	
	def __init__(
			self,
			coordinator: SmarteefiDataUpdateCoordinator,
			device: SmarteefiDevice,
			logger: Logger,
	) -> None:
		"""Init Smarteefi base entity."""
		super().__init__(coordinator)
		
		self.hass = coordinator.hass
		self._device = device
		self._attr_device_info = DeviceInfo(
			identifiers={(DOMAIN, self._get_unique_id())},
			name=self._device.serial,
			manufacturer=MANUFACTURER,
			model=self._device.ip,
		)
		self._logger = logger
	
	def _get_unique_id(
			self, platform: Platform | None = None, suffix: str | None = None
	):
		unique_id = f"{MANUFACTURER}.{self._device.devicename}-{self._device.serial}"
		if suffix:
			unique_id += f"_{suffix}"
		if platform:
			unique_id += f"_{platform}"
		return unique_id
