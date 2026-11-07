"""Sensori: prossima partita e prossimo spettacolo."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import FixturesCoordinator
from .entity import RomaEntity
from .manager import COMPETITIONS

if TYPE_CHECKING:
    from . import RomaConfigEntry

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RomaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Aggiunge i sensori."""
    async_add_entities([NextMatchSensor(entry), NextShowSensor(entry)])


class NextMatchSensor(CoordinatorEntity[FixturesCoordinator], RomaEntity, SensorEntity):
    """Data e ora della prossima partita."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:soccer"

    def __init__(self, entry: RomaConfigEntry) -> None:
        """Inizializza il sensore."""
        CoordinatorEntity.__init__(self, entry.runtime_data.coordinator)
        RomaEntity.__init__(self, entry, "next_match")

    @property
    def native_value(self) -> datetime | None:
        """Calcio d'inizio."""
        match = self.manager.next_match()
        return match.start if match else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Dettagli della partita."""
        match = self.manager.next_match()
        if match is None:
            return {}
        return {
            "match": match.title,
            "opponent": match.opponent,
            "home": match.home,
            "competition": COMPETITIONS.get(match.competition, match.competition)
            if match.competition
            else "Serie A",
            "location": match.location,
            "end": match.end.isoformat(),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


class NextShowSensor(RomaEntity, SensorEntity):
    """Quando partirà il prossimo spettacolo di luci."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:lightbulb-group"
    _attr_should_poll = False

    def __init__(self, entry: RomaConfigEntry) -> None:
        """Inizializza il sensore."""
        super().__init__(entry, "next_show")

    @property
    def native_value(self) -> datetime | None:
        """Orario del prossimo spettacolo."""
        return self.manager.next_show

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Stato dello spettacolo."""
        match = self.manager.next_show_match
        return {
            "match": match.title if match else None,
            "running": self.manager.show_running,
            "last_show": self.manager.last_show.isoformat() if self.manager.last_show else None,
            "presence_ok": self.manager.presence_ok(),
            "song_duration_s": self.manager.song_duration,
        }
