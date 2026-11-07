"""Calendario delle partite dell'AS Roma."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import FixturesCoordinator
from .entity import RomaEntity
from .ics import Match
from .manager import RomaManager

if TYPE_CHECKING:
    from . import RomaConfigEntry

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RomaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Aggiunge il calendario."""
    async_add_entities([RomaCalendar(entry)])


def _event(match: Match) -> CalendarEvent:
    return CalendarEvent(
        start=match.start,
        end=match.end,
        summary=match.summary,
        location=match.location,
        description=RomaManager.describe(match),
        uid=match.uid,
    )


class RomaCalendar(CoordinatorEntity[FixturesCoordinator], RomaEntity, CalendarEntity):
    """Partite della squadra."""

    def __init__(self, entry: RomaConfigEntry) -> None:
        """Inizializza il calendario."""
        CoordinatorEntity.__init__(self, entry.runtime_data.coordinator)
        RomaEntity.__init__(self, entry, "matches")

    @property
    def event(self) -> CalendarEvent | None:
        """Partita in corso o prossima."""
        match = self.manager.next_match()
        return _event(match) if match else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Partite nell'intervallo richiesto."""
        return [
            _event(m)
            for m in self.manager.all_matches
            if m.end > start_date and m.start < end_date
        ]

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
