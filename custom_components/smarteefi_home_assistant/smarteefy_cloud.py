import requests
import json
from .const import *

class SmarteefiAuthAPIResponse:
  _instance = None

  def __new__(cls, *args, **kwargs):
    if not cls._instance:
      cls._instance = super().__new__(cls)
      url = SMARTEEFI_API_URL + "/user/login"

      payload = json.dumps({
        "LoginForm": {
          "email": SMARTEEFI_EMAIL,
          "password": SMARTEEFI_PASSWORD,
          "app": "smarteefi"
        }
      })
      headers = {
        'Content-Type': 'application/json',
      }

      response = requests.request("POST", url, headers=headers, data=payload)
      cls._instance.response_json = response.json()

    return cls._instance


class SmarteefiAPI:
  auth_response = SmarteefiAuthAPIResponse()

  def __init__(self, serialno, switchmap):
    self.serialno = serialno
    self.switchmap = switchmap

  def getStatusFromServer(self, callback):
    # print(self.auth_response.response_json.get('access_token', ''))
    url = SMARTEEFI_API_URL + "/device/getstatus"
    payload = json.dumps({
      "DeviceStatus": {
        "access_token": self.auth_response.response_json.get('access_token', ''),
        "serial": self.serialno,
        "switchmap": self.switchmap
      }
    })
    headers = {
      'Content-Type': 'application/json',
    }
    # response = await hass.async_add_executor_job(requests.request, "POST", url, headers=headers, data=payload)
    response = requests.request("POST", url, headers=headers, data=payload)
    callback(response.json())

  def turn_on_api_call(self):
    url = SMARTEEFI_API_URL + "/device/setstatus"

    payload = json.dumps({
      "DeviceStatus": {
        "access_token": self.auth_response.response_json.get('access_token', ''),
        "serial": self.serialno,
        "switchmap": self.switchmap,
        "statusmap": self.switchmap
      }
    })
    headers = {
      'Content-Type': 'application/json',
    }

    requests.request("POST", url, headers=headers, data=payload)

  def turn_off_api_call(self):
    url = SMARTEEFI_API_URL + "/device/setstatus"

    payload = json.dumps({
      "DeviceStatus": {
        "access_token": self.auth_response.response_json.get('access_token', ''),
        "serial": self.serialno,
        "switchmap": self.switchmap,
        "statusmap": 0
      }
    })
    headers = {
      'Content-Type': 'application/json',
    }

    requests.request("POST", url, headers=headers, data=payload)
