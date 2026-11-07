"""Configurazione guidata di ROMA ROMA ROMA."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowHandler
from homeassistant.helpers.selector import (
    BooleanSelector,
    DeviceSelector,
    DeviceSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_MAX_BRIGHTNESS,
    CONF_MEDIA_PLAYERS,
    CONF_MIN_BRIGHTNESS,
    CONF_NOTIFY_DEVICES,
    CONF_NOTIFY_MINUTES,
    CONF_PERSONS,
    CONF_POWER_ENTITIES,
    CONF_PRESENCE_MODE,
    CONF_RED_LIGHTS,
    CONF_SERIE_A_ONLY,
    CONF_SHOW_MINUTES,
    CONF_SONG,
    CONF_SYNC_OFFSET,
    CONF_YELLOW_LIGHTS,
    DEFAULTS,
    DOMAIN,
    NAME,
    PRESENCE_MODES,
)

LIST_KEYS = (
    CONF_RED_LIGHTS,
    CONF_YELLOW_LIGHTS,
    CONF_POWER_ENTITIES,
    CONF_MEDIA_PLAYERS,
    CONF_NOTIFY_DEVICES,
    CONF_PERSONS,
)


def _percent() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=1, max=100, step=1, unit_of_measurement="%", mode=NumberSelectorMode.SLIDER
        )
    )


def _minutes(maximum: int) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=1, max=maximum, step=1, unit_of_measurement="min", mode=NumberSelectorMode.BOX
        )
    )


LIGHTS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_RED_LIGHTS): EntitySelector(
            EntitySelectorConfig(domain="light", multiple=True)
        ),
        vol.Optional(CONF_YELLOW_LIGHTS): EntitySelector(
            EntitySelectorConfig(domain="light", multiple=True)
        ),
        vol.Optional(CONF_POWER_ENTITIES): EntitySelector(
            EntitySelectorConfig(domain=["switch", "light", "input_boolean"], multiple=True)
        ),
        vol.Required(CONF_MIN_BRIGHTNESS): _percent(),
        vol.Required(CONF_MAX_BRIGHTNESS): _percent(),
    }
)

MEDIA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_MEDIA_PLAYERS): EntitySelector(
            EntitySelectorConfig(domain="media_player", multiple=True)
        ),
        vol.Required(CONF_SONG): TextSelector(),
        vol.Required(CONF_SYNC_OFFSET): NumberSelector(
            NumberSelectorConfig(
                min=0, max=10, step=0.1, unit_of_measurement="s", mode=NumberSelectorMode.BOX
            )
        ),
    }
)

ALERTS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NOTIFY_DEVICES): DeviceSelector(
            DeviceSelectorConfig(integration="mobile_app", multiple=True)
        ),
        vol.Required(CONF_NOTIFY_MINUTES): _minutes(240),
        vol.Required(CONF_SHOW_MINUTES): _minutes(120),
        vol.Optional(CONF_PERSONS): EntitySelector(
            EntitySelectorConfig(domain="person", multiple=True)
        ),
        vol.Required(CONF_PRESENCE_MODE): SelectSelector(
            SelectSelectorConfig(
                options=PRESENCE_MODES,
                translation_key="presence_mode",
                mode=SelectSelectorMode.LIST,
            )
        ),
        vol.Required(CONF_SERIE_A_ONLY): BooleanSelector(),
    }
)


def _merge(data: dict[str, Any], user_input: dict[str, Any], schema: vol.Schema) -> None:
    """Copia l'input; le liste svuotate dall'utente diventano []."""
    for marker in schema.schema:
        key = str(marker)
        if key in user_input:
            data[key] = user_input[key]
        elif key in LIST_KEYS:
            data[key] = []


def _validate_lights(user_input: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not user_input.get(CONF_RED_LIGHTS) and not user_input.get(CONF_YELLOW_LIGHTS):
        errors["base"] = "no_lights"
    elif int(user_input[CONF_MIN_BRIGHTNESS]) >= int(user_input[CONF_MAX_BRIGHTNESS]):
        errors["base"] = "brightness_range"
    return errors


class _Steps(FlowHandler):
    """Passi comuni a configurazione iniziale e opzioni."""

    _data: dict[str, Any]

    async def _lights_step(self, step_id: str, user_input: dict[str, Any] | None):
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = _validate_lights(user_input)
            if not errors:
                _merge(self._data, user_input, LIGHTS_SCHEMA)
                return await self.async_step_media()
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(
                LIGHTS_SCHEMA, {**self._data, **(user_input or {})}
            ),
            errors=errors,
        )

    async def async_step_media(self, user_input: dict[str, Any] | None = None):
        """Canzone e lettori."""
        if user_input is not None:
            _merge(self._data, user_input, MEDIA_SCHEMA)
            return await self.async_step_alerts()
        return self.async_show_form(
            step_id="media",
            data_schema=self.add_suggested_values_to_schema(MEDIA_SCHEMA, self._data),
        )

    async def async_step_alerts(self, user_input: dict[str, Any] | None = None):
        """Telefono, anticipo e presenza."""
        if user_input is not None:
            _merge(self._data, user_input, ALERTS_SCHEMA)
            return self._finish()
        return self.async_show_form(
            step_id="alerts",
            data_schema=self.add_suggested_values_to_schema(ALERTS_SCHEMA, self._data),
        )

    def _finish(self) -> ConfigFlowResult:
        raise NotImplementedError


class RomaConfigFlow(_Steps, ConfigFlow, domain=DOMAIN):
    """Configurazione iniziale."""

    VERSION = 1

    def __init__(self) -> None:
        """Inizializza il flow."""
        self._data = dict(DEFAULTS)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Opzioni modificabili dopo l'installazione."""
        return RomaOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Luci rosse e gialle."""
        return await self._lights_step("user", user_input)

    def _finish(self) -> ConfigFlowResult:
        return self.async_create_entry(title=NAME, data={}, options=self._data)


class RomaOptionsFlow(_Steps, OptionsFlow):
    """Modifica delle opzioni."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Luci rosse e gialle."""
        if not hasattr(self, "_data"):
            self._data = {**DEFAULTS, **self.config_entry.options}
        return await self._lights_step("init", user_input)

    def _finish(self) -> ConfigFlowResult:
        return self.async_create_entry(data=self._data)
