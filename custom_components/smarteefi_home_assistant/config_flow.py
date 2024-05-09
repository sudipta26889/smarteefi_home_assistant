"""Config flow for Smarteefi integration."""

from __future__ import annotations

import logging
from typing import Any, List

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required('serial'): cv.string,
        vol.Required('devname'): cv.string,
        vol.Required('ip'): cv.string,
    }
)


class SmarteefiHAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smarteefi."""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    
    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        coordinator = self.hass.data[DOMAIN]["common_coordinator"]
        await self.hass.async_add_executor_job(coordinator.get_devices)
        
        errors: dict[str, str] = {}
        serial_numbers = list({switch['serial'] for switch in self.hass.data[DOMAIN]["devices"]['modules']})
        already_added_serials = [entry.data['serial'] for entry in self._async_current_entries()]
        not_added_serial_numbers = [serial for serial in serial_numbers if serial not in already_added_serials]
        
        if user_input is not None:
            try:
                info = await self._async_validate_user_input(user_input, already_added_serials)
            except Exception as e:
                _LOGGER.exception("Unexpected exception", e)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)
            
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(
                {
                    vol.Required("serial"): vol.In(
                        not_added_serial_numbers
                    ),
                    vol.Required("devname"): str,
                    vol.Required("ip"): str,
                }
            ), errors=errors
        )
    
    async def _async_validate_user_input(self, user_input: dict[str, Any], already_added_serials: List[str]) -> dict[str, Any]:
        """Validate the user input allows us to connect."""
        if self.hass.data[DOMAIN]["devices"].get('result', 'false') != "success":
            raise vol.Invalid("Failed to get devices from Smarteefi API")
        if not self.hass.data[DOMAIN]["access_token"]:
            raise vol.Invalid("No Access Token Found in hass.data[DOMAIN]['access_token']")
        if not user_input['devname']:
            raise vol.Invalid("Invalid Room Name")
        if not user_input['serial']:
            raise Exception
        if not user_input['ip']:
            raise vol.Invalid("Invalid IP")
        
        if user_input['serial'] in already_added_serials:
            raise vol.Invalid("Serial already added")
        
        title = user_input['devname'] + " - " + user_input['serial']
        return {"title": title}
