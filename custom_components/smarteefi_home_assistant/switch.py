import voluptuous as vol
from homeassistant.components.switch import SwitchEntity, PLATFORM_SCHEMA
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import homeassistant.helpers.config_validation as cv
from typing import Any, Callable, Dict, Optional
from .const import *
import socket
from .smarteefy_cloud import SmarteefiAPI


SWITCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MAP): cv.positive_int,
        vol.Required(CONF_SWITCH_NAME): cv.string
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE_NAME): cv.string,
        vol.Required(CONF_DEVICE_SERIAL): cv.string,
        vol.Required(CONF_GROUP_ID): cv.positive_int,
        vol.Required(CONF_IP): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Required(CONF_SWITCHES): vol.All(cv.ensure_list, [SWITCH_SCHEMA])
    }
)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the switch platform."""

    smarteefy_module = SmarteefyModule(config.get(CONF_DEVICE_NAME), config.get(CONF_DEVICE_SERIAL), config.get(CONF_GROUP_ID), config.get(CONF_IP), config.get(CONF_PORT))
    switches = [SmarteefiSwitch(smarteefy_module, eachSwitchInModule[CONF_MAP], eachSwitchInModule[CONF_SWITCH_NAME]) for eachSwitchInModule in config[CONF_SWITCHES]]

    for eachSwitch in switches:
        await hass.async_add_executor_job(eachSwitch.getStatusFromServer)
    async_add_entities(switches, update_before_add=True)

class SmarteefyModule:
    def __init__(self, devicename, serial, group_id, ip, port=10201):
        self.devicename = devicename
        self.serial = serial
        self.group_id = group_id
        self.ip = ip
        self.port = port

class SmarteefiSwitch(SwitchEntity):

    def __init__(self, smarteefy_module: SmarteefyModule, map_id, switchname):
        
        self.type = "switch"
        self.map = map_id
        self.ownership = "owned"
        self.selfshared = False
        self.switchname = switchname
        self.smarteefy_module = smarteefy_module
        self._attr_unique_id = (
            f"Smarteefi {self.smarteefy_module.serial}-{self.map} Switch {self.switchname}"
        )
        self.cloud_api = SmarteefiAPI(self.smarteefy_module.serial, self.map)
        self.statusmap = 0


    @property
    def name(self):
        return self.switchname

    @property
    def is_on(self):
        return True if self.statusmap else False

    def getStatusFromServer(self):
        # hass.async_add_executor_job(self.cloud_api.getStatusFromServer)
        self.cloud_api.getStatusFromServer(self.updateStatus)

    def updateStatus(self, cloud_response):
        # print(cloud_response)
        self.statusmap = cloud_response.get('statusmap', 0)

    def turn_on(self):
        # Logic to turn on the switch
        self.statusmap = self.map
        deviceId = self.smarteefy_module.serial
        switchMap = str(int(self.map))
        statusMap = str(int(self.statusmap))
        self.send_hex_command(self.smarteefy_module.ip, int(self.smarteefy_module.port), deviceId, switchMap, statusMap)
        self.cloud_api.turn_on_api_call()
        

    def turn_off(self):
        # Logic to turn off the switch
        self.statusmap = 0
        deviceId = self.smarteefy_module.serial
        switchMap = str(int(self.map))
        statusMap = str(self.statusmap)
        self.send_hex_command(self.smarteefy_module.ip, int(self.smarteefy_module.port), deviceId, switchMap, statusMap)
        self.cloud_api.turn_off_api_call()

    def send_hex_command(self, ip, port, deviceId, switchMap, statusMap):
        # print(" DeviceId: %s Map: %s, Status: %s, IP: %s, Port: %s" % (deviceId, switchMap, statusMap, ip, port))
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


