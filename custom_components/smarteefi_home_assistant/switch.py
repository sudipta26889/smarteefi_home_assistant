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
from .smarteefy_cloud import SmarteefiAPI, SmarteefiAuthAPIResponse


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required('email'): cv.string,
        vol.Required('password'): cv.string
    }
)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the switch platform."""
    
    smarteefy_cloud_auth = await hass.async_add_executor_job(SmarteefiAuthAPIResponse, config['email'], config['password'])
    # smarteefy_cloud_auth = SmarteefiAuthAPIResponse(config['email'], config['password'])
    

    cloud_response = await hass.async_add_executor_job(SmarteefiAPI.getDevices, smarteefy_cloud_auth.response_json.get('access_token', ''))

    switches = []

    # print(cloud_response)
    for each_module in cloud_response.get('modules', []):
        group_id =  ""
        for each_switch in cloud_response.get('switches', []):
            if each_switch['serial'] == each_module['serial']:
                group_id = each_switch['group_id']
                break
        more_device_info = await hass.async_add_executor_job(SmarteefiAPI.getDeviceMoreInfo, smarteefy_cloud_auth.response_json.get('access_token', ''), each_module['serial'])
        # print(more_device_info)
        smarteefy_module = SmarteefyModule(each_module['devname'], each_module['serial'], group_id, more_device_info['dev_ip'], more_device_info['dev_port'])
        for each_switch in cloud_response.get('switches', []):
            if each_switch['serial'] == each_module['serial']:
                switches.append(
                    SmarteefiSwitch(smarteefy_module, each_switch['map'], each_switch['name'], smarteefy_cloud_auth.response_json.get('access_token', ''))
                )
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

    def __init__(self, smarteefy_module: SmarteefyModule, map_id, switchname, smarteefy_cloud_auth):
        self.type = "switch"
        self.map = map_id
        self.ownership = "owned"
        self.selfshared = False
        self.switchname = switchname
        self.smarteefy_module = smarteefy_module
        self._attr_unique_id = (
            f"Smarteefi {self.smarteefy_module.serial}-{self.map} Switch {self.switchname}"
        )
        self._attr_entity_id = smarteefy_module.serial + "-" + str(self.map)
        # print(smarteefy_cloud_auth)
        self.cloud_api = SmarteefiAPI(smarteefy_cloud_auth, self.smarteefy_module.serial, self.map)
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


