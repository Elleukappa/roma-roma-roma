"""Interruttori per attivare/disattivare avvisi e spettacolo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .entity import RomaEntity

if TYPE_CHECKING:
    from . import RomaConfigEntry

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RomaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Aggiunge gli interruttori."""
    async_add_entities([NotifySwitch(entry), ShowSwitch(entry)])


class _FlagSwitch(RomaEntity, SwitchEntity, RestoreEntity):
    _attr_should_poll = False
    _flag: str

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            setattr(self.manager, self._flag, last.state != STATE_OFF)

    @property
    def is_on(self) -> bool:
        return bool(getattr(self.manager, self._flag))

    async def async_turn_on(self, **kwargs: Any) -> None:
        setattr(self.manager, self._flag, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        setattr(self.manager, self._flag, False)
        self.async_write_ha_state()


class NotifySwitch(_FlagSwitch):
    """Avviso sul telefono prima della partita."""

    _attr_icon = "mdi:cellphone-message"
    _flag = "notify_enabled"

    def __init__(self, entry: RomaConfigEntry) -> None:
        """Inizializza l'interruttore."""
        super().__init__(entry, "notify_enabled")


class ShowSwitch(_FlagSwitch):
    """Spettacolo di luci e inno prima della partita."""

    _attr_icon = "mdi:party-popper"
    _flag = "show_enabled"

    def __init__(self, entry: RomaConfigEntry) -> None:
        """Inizializza l'interruttore."""
        super().__init__(entry, "show_enabled")
