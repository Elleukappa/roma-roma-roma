"""ROMA ROMA ROMA: avvisi delle partite dell'AS Roma e spettacolo di luci giallorosso."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import FixturesCoordinator
from .manager import RomaManager
from .services import async_setup_services

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.CALENDAR,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass
class RomaData:
    """Dati condivisi della config entry."""

    coordinator: FixturesCoordinator
    manager: RomaManager


type RomaConfigEntry = ConfigEntry[RomaData]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Registra i servizi dell'integrazione."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: RomaConfigEntry) -> bool:
    """Configura l'integrazione da una config entry."""
    coordinator = FixturesCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    manager = RomaManager(hass, entry, coordinator)
    await manager.async_setup()
    entry.runtime_data = RomaData(coordinator=coordinator, manager=manager)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RomaConfigEntry) -> bool:
    """Scarica la config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.manager.async_unload()
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: RomaConfigEntry) -> None:
    """Ricarica quando cambiano le opzioni."""
    await hass.config_entries.async_reload(entry.entry_id)
