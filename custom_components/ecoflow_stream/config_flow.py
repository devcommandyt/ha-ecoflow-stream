"""Config flow: access key, secret key and serial number from developer.ecoflow.com."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EcoflowError, get_certification
from .const import CONF_ACCESS_KEY, CONF_SECRET_KEY, CONF_SN, DOMAIN


class EcoflowStreamConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            user_input[CONF_SN] = user_input[CONF_SN].strip()
            await self.async_set_unique_id(user_input[CONF_SN])
            self._abort_if_unique_id_configured()
            try:
                await get_certification(async_get_clientsession(self.hass),
                                        user_input[CONF_ACCESS_KEY].strip(), user_input[CONF_SECRET_KEY].strip())
            except EcoflowError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=f"EcoFlow STREAM {user_input[CONF_SN][-4:]}", data=user_input)
        schema = vol.Schema({
            vol.Required(CONF_ACCESS_KEY): str,
            vol.Required(CONF_SECRET_KEY): str,
            vol.Required(CONF_SN): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
