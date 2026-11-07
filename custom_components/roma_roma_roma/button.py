"""Pulsanti di prova."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import RomaEntity

if TYPE_CHECKING:
    from . import RomaConfigEntry

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RomaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Aggiunge i pulsanti."""
    async_add_entities(
        [StartShowButton(entry), StopShowButton(entry), TestNotificationButton(entry)]
    )


class StartShowButton(RomaEntity, ButtonEntity):
    """Avvia subito spettacolo e canzone."""

    _attr_icon = "mdi:play-circle"

    def __init__(self, entry: RomaConfigEntry) -> None:
        """Inizializza il pulsante."""
        super().__init__(entry, "start_show")

    async def async_press(self) -> None:
        """Avvia lo spettacolo."""
        self.manager.async_start_show(play_song=True)


class StopShowButton(RomaEntity, ButtonEntity):
    """Ferma lo spettacolo."""

    _attr_icon = "mdi:stop-circle"

    def __init__(self, entry: RomaConfigEntry) -> None:
        """Inizializza il pulsante."""
        super().__init__(entry, "stop_show")

    async def async_press(self) -> None:
        """Ferma lo spettacolo."""
        await self.manager.async_stop_show()


class TestNotificationButton(RomaEntity, ButtonEntity):
    """Invia una notifica di prova."""

    _attr_icon = "mdi:bell-ring"

    def __init__(self, entry: RomaConfigEntry) -> None:
        """Inizializza il pulsante."""
        super().__init__(entry, "test_notification")

    async def async_press(self) -> None:
        """Invia la notifica."""
        await self.manager.async_test_notification()
