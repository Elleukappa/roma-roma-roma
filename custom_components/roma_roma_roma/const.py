"""Costanti per ROMA ROMA ROMA."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "roma_roma_roma"
NAME: Final = "ROMA ROMA ROMA"

# Squadra fissa: calendario AS Roma (Serie A, coppe europee, Coppa Italia...).
FIXTURES_URL: Final = "https://ics.fixtur.es/v2/as-roma.ics"
UPDATE_INTERVAL: Final = timedelta(hours=6)

# Canzone fissa: lo spettacolo di luci è calcolato su questa registrazione.
SONG_TITLE: Final = "Antonello Venditti - Roma Roma Roma"
DEFAULT_SONG: Final = "media-source://media_source/local/Antonello Venditti - Roma Roma Roma.mp3"
SONG_CONTENT_TYPE: Final = "audio/mpeg"

# Colori fissi della squadra.
COLOR_RED: Final = (255, 0, 0)
COLOR_YELLOW: Final = (255, 200, 0)

# Opzioni
CONF_RED_LIGHTS: Final = "red_lights"
CONF_YELLOW_LIGHTS: Final = "yellow_lights"
CONF_POWER_ENTITIES: Final = "power_entities"
CONF_MEDIA_PLAYERS: Final = "media_players"
CONF_SONG: Final = "song_media_id"
CONF_SYNC_OFFSET: Final = "sync_offset"
CONF_MIN_BRIGHTNESS: Final = "min_brightness"
CONF_MAX_BRIGHTNESS: Final = "max_brightness"
CONF_NOTIFY_DEVICES: Final = "notify_devices"
CONF_NOTIFY_MINUTES: Final = "notify_minutes"
CONF_SHOW_MINUTES: Final = "show_minutes"
CONF_PERSONS: Final = "persons"
CONF_PRESENCE_MODE: Final = "presence_mode"
CONF_SERIE_A_ONLY: Final = "serie_a_only"
CONF_RESTORE_LIGHTS: Final = "restore_lights"

PRESENCE_HOME: Final = "home"
PRESENCE_HOME_OR_UNKNOWN: Final = "home_or_unknown"
PRESENCE_ALWAYS: Final = "always"
PRESENCE_MODES: Final = [PRESENCE_HOME, PRESENCE_HOME_OR_UNKNOWN, PRESENCE_ALWAYS]

DEFAULTS: Final = {
    CONF_RED_LIGHTS: [],
    CONF_YELLOW_LIGHTS: [],
    CONF_POWER_ENTITIES: [],
    CONF_MEDIA_PLAYERS: [],
    CONF_SONG: DEFAULT_SONG,
    CONF_SYNC_OFFSET: 0.5,
    CONF_MIN_BRIGHTNESS: 10,
    CONF_MAX_BRIGHTNESS: 100,
    CONF_NOTIFY_DEVICES: [],
    CONF_NOTIFY_MINUTES: 30,
    CONF_SHOW_MINUTES: 10,
    CONF_PERSONS: [],
    CONF_PRESENCE_MODE: PRESENCE_HOME_OR_UNKNOWN,
    CONF_SERIE_A_ONLY: False,
    CONF_RESTORE_LIGHTS: True,
}

# Tempi dello spettacolo
POWER_ON_TIMEOUT: Final = 90  # secondi di attesa perché le luci tornino disponibili
PLAYBACK_START_TIMEOUT: Final = 10  # secondi di attesa che la canzone parta
LIGHT_TRANSITION: Final = 0.25
MAX_LATE_FRAME: Final = 0.4  # un fotogramma in ritardo oltre questo viene saltato

SERVICE_START_SHOW: Final = "start_show"
SERVICE_STOP_SHOW: Final = "stop_show"
SERVICE_TEST_NOTIFICATION: Final = "test_notification"
ATTR_PLAY_SONG: Final = "play_song"
ATTR_OFFSET: Final = "offset"

SIGNAL_STATE_UPDATED: Final = f"{DOMAIN}_state_updated"

# Notifica "inno in corso" con pulsante Ferma (app Home Assistant)
NOTIFICATION_TAG: Final = DOMAIN
NOTIFICATION_STOP_ACTION: Final = "ROMA_ROMA_ROMA_STOP"
EVENT_NOTIFICATION_ACTION: Final = "mobile_app_notification_action"
RESTORE_TRANSITION: Final = 2
