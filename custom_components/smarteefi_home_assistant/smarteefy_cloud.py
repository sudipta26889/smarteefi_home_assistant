import json
from logging import getLogger

import requests

from homeassistant.core import HomeAssistant
from .const import *

_LOGGER = getLogger(__name__)


class SmarteefiAuthAPIResponse:
	_instance = None
	
	def __new__(cls, hass: HomeAssistant, email, password):
		if not cls._instance:
			cls._instance = super().__new__(cls)
			url = SMARTEEFI_API_URL + "/user/login"
			
			payload = json.dumps({
				"LoginForm": {
					"email": email,
					"password": password,
					"app": "smarteefi"
				}
			})
			headers = {
				'Content-Type': 'application/json',
			}
			
			response = requests.request("POST", url, headers=headers, data=payload)
			cls._instance.response_json = response.json()
		hass.data[DOMAIN]["access_token"] = cls._instance.response_json.get("access_token", "")
		return cls._instance


class SmarteefiAPI:
	
	def __init__(self, hass: HomeAssistant):
		self._hass = hass
		self._base_url = SMARTEEFI_API_URL
	
	@property
	def access_token(self):
		_LOGGER.debug("debug-log-1:: %s" % self._hass.data[DOMAIN])
		
		return self._hass.data[DOMAIN]["access_token"]
	
	async def turn_on_api_call(self, serialno, switchmap):
		url = SMARTEEFI_API_URL + "/device/setstatus"
		
		payload = json.dumps({
			"DeviceStatus": {
				"access_token": self.access_token,
				"duration": 0,
				"serial": serialno,
				"statusmap": switchmap,
				"switchmap": switchmap
			}
		})
		headers = {
			'Content-Type': 'application/json',
		}
		
		def turn_on_request(url, headers, payload):
			requests.request("POST", url, headers=headers, data=payload)
		
		await self._hass.async_add_executor_job(turn_on_request, url, headers, payload)
	
	# requests.request("POST", url, headers=headers, data=payload)
	
	async def turn_off_api_call(self, serialno, switchmap):
		url = SMARTEEFI_API_URL + "/device/setstatus"
		
		payload = json.dumps({
			"DeviceStatus": {
				"access_token": self.access_token,
				"duration": 0,
				"serial": serialno,
				"statusmap": 0,
				"switchmap": switchmap
			}
		})
		headers = {
			'Content-Type': 'application/json',
		}
		
		def turn_off_request(url, headers, payload):
			requests.request("POST", url, headers=headers, data=payload)
		
		await self._hass.async_add_executor_job(turn_off_request, url, headers, payload)
	
	def getDevices(self):
		url = SMARTEEFI_API_URL + "/user/devices"
		
		payload = json.dumps({
			"UserDevice": {
				"access_token": self.access_token
			}
		})
		headers = {
			'Content-Type': 'application/json',
		}
		
		response = requests.request("POST", url, headers=headers, data=payload)
		
		return response.json()
	
	def getDeviceMoreInfo(self, serial, switchmap=0):
		url = SMARTEEFI_API_URL + "/device/getstatus"
		payload = json.dumps({
			"DeviceStatus": {
				"access_token": self.access_token,
				"serial": serial,
				"switchmap": switchmap
			}
		})
		headers = {
			'Content-Type': 'application/json',
		}
		# print("payload -> ", payload)
		response = requests.request("POST", url, headers=headers, data=payload)
		response_json = response.json()
		
		if response_json.get('result', 'error') != "success":
			print("getDeviceMoreInfo error response_json -> ", response_json)
		return response_json
