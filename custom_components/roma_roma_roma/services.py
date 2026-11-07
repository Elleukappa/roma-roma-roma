"""Servizi di ROMA ROMA ROMA."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_OFFSET,
    ATTR_PLAY_SONG,
    DOMAIN,
    SERVICE_START_SHOW,
    SERVICE_STOP_SHOW,
    SERVICE_TEST_NOTIFICATION,
)

if TYPE_CHECKING:
    from .manager import RomaManager

START_SHOW_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_PLAY_SONG, default=True): cv.boolean,
        vol.Optional(ATTR_OFFSET): vol.All(vol.Coerce(float), vol.Range(min=0, max=30)),
    }
)


def _manager(hass: HomeAssistant) -> RomaManager:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data.manager
    raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Registra i servizi."""

    async def start_show(call: ServiceCall) -> None:
        _manager(hass).async_start_show(
            play_song=call.data[ATTR_PLAY_SONG], offset=call.data.get(ATTR_OFFSET)
        )

    async def stop_show(call: ServiceCall) -> None:
        await _manager(hass).async_stop_show()

    async def test_notification(call: ServiceCall) -> None:
        await _manager(hass).async_test_notification()

    hass.services.async_register(DOMAIN, SERVICE_START_SHOW, start_show, START_SHOW_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP_SHOW, stop_show)
    hass.services.async_register(DOMAIN, SERVICE_TEST_NOTIFICATION, test_notification)
