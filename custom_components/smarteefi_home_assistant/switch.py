import asyncio
import socket
from logging import getLogger
from typing import Any, Callable, Optional

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import SwitchEntity, PLATFORM_SCHEMA
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import (
	ConfigType,
	DiscoveryInfoType,
)
from . import SmarteefiDataUpdateCoordinator
from .const import DOMAIN
from .device import SmarteefiDevice
from .entity import SmarteefiEntity, platform_async_setup_entry
from .smarteefy_cloud import SmarteefiAPI, SmarteefiAuthAPIResponse

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
	{
		vol.Required('email'): cv.string,
		vol.Required('password'): cv.string
	}
)

_LOGGER = getLogger(__name__)


async def async_setup_platform(
		hass: HomeAssistant,
		config: ConfigType,
		async_add_entities: Callable,
		discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
	"""
	Get config from configuration.yaml.
	switch:
	  - platform: smarteefi_home_assistant
	    email: "<email>"
	    password: "<password>"

	And set hass.data[DOMAIN]["access_token"] for further use."""
	# print("switch async_setup_platform called")
	hass.data.setdefault(DOMAIN, {})
	await hass.async_add_executor_job(SmarteefiAuthAPIResponse, hass, config['email'], config['password'])
	api = SmarteefiAPI(hass)
	coordinator = SmarteefiDataUpdateCoordinator(hass=hass, api=api)
	hass.data[DOMAIN]["common_coordinator"] = coordinator
	await hass.async_add_executor_job(api.getDevices)
	entries = hass.config_entries.async_entries(DOMAIN)
	# print("entry in async_setup_platform", entries)
	if entries is not None:
		for entry in entries:
			hass.async_create_task(
				hass.config_entries.async_reload(entry.entry_id)
			)


async def async_setup_entry(
		hass: HomeAssistant,
		config_entry: ConfigEntry,
		async_add_entities: AddEntitiesCallback,
) -> None:
	"""Automatically setup the switch entities from the devices list."""
	# print("switch async_setup_entry called")
	await platform_async_setup_entry(
		hass, config_entry, async_add_entities, SmarteefiSwitchEntity
	)


class SmarteefiSwitchEntity(SmarteefiEntity, SwitchEntity):
	
	def __init__(self, coordinator: SmarteefiDataUpdateCoordinator, device: SmarteefiDevice, map_id, switchname, cloud_statusmap=None):
		super().__init__(coordinator, device, _LOGGER)
		# print("switch SmarteefiSwitchEntity init called")
		self.type = "switch"
		self.map = map_id
		self.ownership = "owned"
		self.selfshared = False
		self.switchname = switchname
		self.smarteefy_module = device
		self._attr_unique_id = (
			f"Smarteefi {self.smarteefy_module.serial}-{self.map} Switch {self.switchname}"
		)
		self._attr_entity_id = device.serial + "-" + str(self.map)
		self.statusmap = cloud_statusmap if cloud_statusmap else 0
		self._state = True if self.statusmap else False
		self.hass = self.smarteefy_module.hass
		self.cloud_api = SmarteefiAPI(self.hass)
	
	@property
	def name(self):
		return self.switchname
	
	@property
	def is_on(self):
		self._state = True if self.statusmap else False
		# print("self.statusmap (%s) --->> %s" % (self._attr_unique_id, self.statusmap))
		return self._state
	
	def updateStatus(self, cloud_response):
		# print(cloud_response)
		self.statusmap = cloud_response.get('statusmap', 0)
	
	async def async_turn_on(self, **kwargs: Any) -> None:
		# Logic to turn on the switch
		self.statusmap = self.map
		deviceId = self.smarteefy_module.serial
		switchMap = str(int(self.map))
		statusMap = str(int(self.statusmap))
		self._state = True
		# print("switchMap: %s | statusMap: %s " % (switchMap, statusMap))
		self.__send_hex_command(self.smarteefy_module.ip, int(self.smarteefy_module.port), deviceId, switchMap,
		                        statusMap)
		asyncio.create_task(self.cloud_api.turn_on_api_call(self.smarteefy_module.serial, self.map))
		# await self.hass.async_add_executor_job(self.cloud_api.turn_on_api_call, self.smarteefy_module.serial, self.map)
		# self.cloud_api.turn_on_api_call(self.smarteefy_module.serial, self.map)
		self.schedule_update_ha_state()
	
	async def async_turn_off(self, **kwargs: Any) -> None:
		# Logic to turn off the switch
		self.statusmap = 0
		deviceId = self.smarteefy_module.serial
		switchMap = str(int(self.map))
		statusMap = str(self.statusmap)
		self._state = False
		self.__send_hex_command(self.smarteefy_module.ip, int(self.smarteefy_module.port), deviceId, switchMap,
		                        statusMap)
		asyncio.create_task(self.cloud_api.turn_off_api_call(self.smarteefy_module.serial, self.map))
		# await self.hass.async_add_executor_job(self.cloud_api.turn_off_api_call, self.smarteefy_module.serial, self.map)
		# self.cloud_api.turn_off_api_call(self.smarteefy_module.serial, self.map)
		self.schedule_update_ha_state()
	
	def __send_hex_command(self, ip, port, deviceId, switchMap, statusMap):
		_LOGGER.info(" DeviceId: %s Map: %s, Status: %s, IP: %s, Port: %s" % (deviceId, switchMap, statusMap, ip, port))
		hex_command = (
				"cc 10 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
				+ deviceId.encode("utf-8").hex()
				+ " 00 00 00 00 00 00 00 00 00 00 00 00 "
				+ switchMap.encode("utf-8").hex()
				+ " 00 00 00 "
				+ statusMap.encode("utf-8").hex()
				+ " 00 00 00 00 00 00 00 00 00 00 00"
		)
		
		# Create a socket object
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
		# Convert the hex string to bytes
		command_bytes = bytes.fromhex(hex_command)
		
		# Send the command
		sock.sendto(command_bytes, (ip, port))
		
		# Close the socket
		sock.close()
