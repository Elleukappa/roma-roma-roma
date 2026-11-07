"""Entità base di ROMA ROMA ROMA."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, NAME, SIGNAL_STATE_UPDATED

if TYPE_CHECKING:
    from . import RomaConfigEntry


class RomaEntity(Entity):
    """Entità collegata al dispositivo di servizio ROMA ROMA ROMA."""

    _attr_has_entity_name = True

    def __init__(self, entry: RomaConfigEntry, key: str) -> None:
        """Inizializza l'entità."""
        self.entry = entry
        self.manager = entry.runtime_data.manager
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="Tifosi giallorossi",
            model="AS Roma: calendario e spettacolo luci",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Si aggiorna quando il manager cambia stato."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_STATE_UPDATED}_{self.entry.entry_id}",
                self._handle_manager_update,
            )
        )

    @callback
    def _handle_manager_update(self) -> None:
        self.async_write_ha_state()
