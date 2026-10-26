"""EcoFlow STREAM microinverter (cloud MQTT) for Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util.ssl import get_default_context

from .api import EcoflowStreamClient
from .const import CONF_ACCESS_KEY, CONF_SECRET_KEY, CONF_SN, DOMAIN

PLATFORMS = ["sensor"]


def signal(entry_id: str) -> str:
    return f"{DOMAIN}_update_{entry_id}"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = {"data": {}, "connected": False}
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = store

    def on_data(update: dict) -> None:
        store["data"].update(update)
        async_dispatcher_send(hass, signal(entry.entry_id))

    def on_state(connected: bool) -> None:
        store["connected"] = connected
        async_dispatcher_send(hass, signal(entry.entry_id))

    client = EcoflowStreamClient(
        async_get_clientsession(hass), get_default_context(),
        entry.data[CONF_ACCESS_KEY], entry.data[CONF_SECRET_KEY], entry.data[CONF_SN], on_data, on_state)
    entry.async_create_background_task(hass, client.run(), "ecoflow_stream_mqtt")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
