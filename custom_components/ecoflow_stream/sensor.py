"""Sensors fed by the MQTT updates. Long-term statistics are recorded by Home Assistant."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfElectricPotential, UnitOfPower, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import signal
from .const import CONF_SN, DOMAIN

# (field in the MQTT payload, name, unit, device class)
SENSORS = [
    ("gridConnectionPower", "Grid feed-in power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    ("powGetPv2", "Solar input 2 power", UnitOfPower.WATT, SensorDeviceClass.POWER),
    ("gridConnectionVol", "Grid voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
    ("invNtcTemp3", "Inverter temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
]


async def async_setup_entry(hass, entry, async_add_entities):
    store = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(EcoflowSensor(entry, store, *s) for s in SENSORS)


class EcoflowSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry, store, key, name, unit, device_class) -> None:
        self._entry = entry
        self._store = store
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        sn = entry.data[CONF_SN]
        self._attr_unique_id = f"{sn}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sn)}, name="EcoFlow STREAM", manufacturer="EcoFlow",
            model="STREAM microinverter", serial_number=sn)

    @property
    def native_value(self):
        return self._store["data"].get(self._key)

    @property
    def available(self) -> bool:
        return self._store["connected"] or self._key in self._store["data"]

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(
            self.hass, signal(self._entry.entry_id), self.async_write_ha_state))
