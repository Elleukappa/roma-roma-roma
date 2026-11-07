"""Coordinator che scarica il calendario delle partite."""

from __future__ import annotations

import asyncio
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, FIXTURES_URL, UPDATE_INTERVAL
from .ics import Match, parse_ics

_LOGGER = logging.getLogger(__name__)


class FixturesCoordinator(DataUpdateCoordinator[list[Match]]):
    """Scarica e interpreta il calendario ICS della squadra."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Inizializza il coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> list[Match]:
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(30):
                response = await session.get(FIXTURES_URL)
                response.raise_for_status()
                text = await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Calendario non raggiungibile: {err}") from err
        default_tz = dt_util.get_default_time_zone()
        matches = await self.hass.async_add_executor_job(parse_ics, text, default_tz)
        if not matches:
            raise UpdateFailed("Il calendario non contiene partite")
        return matches
