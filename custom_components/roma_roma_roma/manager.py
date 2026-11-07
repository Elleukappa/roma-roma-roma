"""Logica principale: pianifica avvisi e spettacolo di luci per ogni partita."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_HOME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util, slugify

from .const import (
    COLOR_RED,
    COLOR_YELLOW,
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
    LIGHT_TRANSITION,
    MAX_LATE_FRAME,
    PLAYBACK_START_TIMEOUT,
    POWER_ON_TIMEOUT,
    PRESENCE_ALWAYS,
    PRESENCE_HOME_OR_UNKNOWN,
    SIGNAL_STATE_UPDATED,
    SONG_CONTENT_TYPE,
)
from .coordinator import FixturesCoordinator
from .frames import Frame, build_frames, load_beatmap
from .ics import Match

_LOGGER = logging.getLogger(__name__)

COMPETITIONS = {
    "CL": "Champions League",
    "EL": "Europa League",
    "ECL": "Conference League",
    "CONF": "Conference League",
    "CI": "Coppa Italia",
    "COP": "Coppa Italia",
    "SC": "Supercoppa",
}

TEXTS = {
    "it": {
        "title": "⚽ Forza Roma!",
        "soon": "Tra {minutes} minuti: {match} alle {time}",
        "next": "Prossima partita: {match} il {date} alle {time}",
        "none": "Nessuna partita in calendario.",
    },
    "en": {
        "title": "⚽ Forza Roma!",
        "soon": "In {minutes} minutes: {match} at {time}",
        "next": "Next match: {match} on {date} at {time}",
        "none": "No match in the calendar.",
    },
}


class RomaManager:
    """Gestisce pianificazione, notifiche e spettacolo."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, coordinator: FixturesCoordinator
    ) -> None:
        """Inizializza il manager."""
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self.notify_enabled = True
        self.show_enabled = True
        self.next_notify: datetime | None = None
        self.next_show: datetime | None = None
        self.next_show_match: Match | None = None
        self.last_show: datetime | None = None
        self._timers: list[Callable[[], None]] = []
        self._unsub_coordinator: Callable[[], None] | None = None
        self._show_task: asyncio.Task | None = None
        self._beatmap: dict[str, Any] = {}

    # ------------------------------------------------------------------ setup
    async def async_setup(self) -> None:
        """Carica la mappa delle battute e avvia la pianificazione."""
        self._beatmap = await self.hass.async_add_executor_job(load_beatmap)
        self._unsub_coordinator = self.coordinator.async_add_listener(self.async_reschedule)
        self.async_reschedule()

    async def async_unload(self) -> None:
        """Ferma timer e spettacolo."""
        self._cancel_timers()
        if self._unsub_coordinator:
            self._unsub_coordinator()
            self._unsub_coordinator = None
        await self.async_stop_show()

    @property
    def options(self) -> dict[str, Any]:
        """Opzioni correnti con i valori di default."""
        return {**DEFAULTS, **self.entry.options}

    @property
    def show_running(self) -> bool:
        """True se lo spettacolo è in corso."""
        return self._show_task is not None and not self._show_task.done()

    @property
    def song_duration(self) -> float:
        """Durata della canzone su cui è calcolato lo spettacolo."""
        return float(self._beatmap.get("duration", 0))

    # ------------------------------------------------------------- calendario
    @property
    def all_matches(self) -> list[Match]:
        """Tutte le partite del calendario."""
        return self.coordinator.data or []

    @property
    def alert_matches(self) -> list[Match]:
        """Partite per cui inviare avvisi (eventuale filtro solo Serie A)."""
        if self.options[CONF_SERIE_A_ONLY]:
            return [m for m in self.all_matches if m.is_league]
        return self.all_matches

    def next_match(self, now: datetime | None = None) -> Match | None:
        """Partita in corso o prossima."""
        now = now or dt_util.utcnow()
        return next((m for m in self.all_matches if m.end > now), None)

    # ---------------------------------------------------------- pianificazione
    def _cancel_timers(self) -> None:
        while self._timers:
            self._timers.pop()()

    @callback
    def async_reschedule(self) -> None:
        """Pianifica il prossimo avviso e il prossimo spettacolo."""
        self._cancel_timers()
        now = dt_util.utcnow()
        opts = self.options
        notify_delta = timedelta(minutes=float(opts[CONF_NOTIFY_MINUTES]))
        show_delta = timedelta(minutes=float(opts[CONF_SHOW_MINUTES]))
        self.next_notify = self.next_show = None
        self.next_show_match = None

        for match in self.alert_matches:
            when = match.start - notify_delta
            if when > now:
                self.next_notify = when
                self._timers.append(
                    async_track_point_in_utc_time(
                        self.hass, self._make_notify_job(match, opts), when
                    )
                )
                break
        for match in self.alert_matches:
            when = match.start - show_delta
            if when > now:
                self.next_show = when
                self.next_show_match = match
                self._timers.append(
                    async_track_point_in_utc_time(self.hass, self._make_show_job(match), when)
                )
                break
        _LOGGER.debug("Prossimo avviso %s, prossimo spettacolo %s", self.next_notify, self.next_show)
        self._signal()

    def _make_notify_job(self, match: Match, opts: dict[str, Any]):
        async def _job(_now: datetime) -> None:
            if self.notify_enabled:
                await self.async_notify_match(match, int(float(opts[CONF_NOTIFY_MINUTES])))
            self.async_reschedule()

        return _job

    def _make_show_job(self, match: Match):
        async def _job(_now: datetime) -> None:
            if not self.show_enabled:
                _LOGGER.info("Spettacolo disattivato: salto %s", match.summary)
            elif not self.presence_ok():
                _LOGGER.info("Nessuno in casa: salto lo spettacolo per %s", match.summary)
            else:
                self.async_start_show(play_song=True)
            self.async_reschedule()

        return _job

    # ---------------------------------------------------------------- presenza
    def presence_ok(self) -> bool:
        """Verifica la condizione di presenza scelta."""
        opts = self.options
        persons: list[str] = opts[CONF_PERSONS]
        mode = opts[CONF_PRESENCE_MODE]
        if not persons or mode == PRESENCE_ALWAYS:
            return True
        states = [s.state if (s := self.hass.states.get(p)) else STATE_UNKNOWN for p in persons]
        if any(state == STATE_HOME for state in states):
            return True
        return mode == PRESENCE_HOME_OR_UNKNOWN and all(
            state in (STATE_UNKNOWN, STATE_UNAVAILABLE) for state in states
        )

    # ------------------------------------------------------------------ notify
    def _texts(self) -> dict[str, str]:
        lang = (self.hass.config.language or "en").split("-")[0]
        return TEXTS.get(lang, TEXTS["en"])

    @staticmethod
    def describe(match: Match) -> str:
        """Testo leggibile della partita, con competizione e stadio."""
        text = match.title
        if match.competition:
            text += f" ({COMPETITIONS.get(match.competition, match.competition)})"
        if match.location:
            text += f" – {match.location}"
        return text

    def notify_services(self) -> list[str]:
        """Servizi notify.mobile_app_* dei telefoni scelti."""
        dev_reg = dr.async_get(self.hass)
        services: list[str] = []
        for device_id in self.options[CONF_NOTIFY_DEVICES]:
            device = dev_reg.async_get(device_id)
            if device is None:
                continue
            # HA >= 2026.x: un dispositivo appartiene a una sola config entry
            entry_ids = (
                [device.config_entry_id]
                if hasattr(device, "config_entry_id")
                else list(device.config_entries)
            )
            for entry_id in entry_ids:
                entry = self.hass.config_entries.async_get_entry(entry_id)
                if entry is None or entry.domain != "mobile_app":
                    continue
                name = entry.data.get("device_name") or device.name or ""
                service = f"mobile_app_{slugify(name)}"
                if self.hass.services.has_service("notify", service):
                    services.append(service)
                else:
                    _LOGGER.warning("Servizio notify.%s non trovato", service)
        return services

    async def _send(self, message: str) -> None:
        title = self._texts()["title"]
        for service in self.notify_services():
            try:
                await self.hass.services.async_call(
                    "notify", service, {"title": title, "message": message}, blocking=True
                )
            except Exception:  # noqa: BLE001 - un telefono non deve bloccare gli altri
                _LOGGER.exception("Invio notifica con notify.%s fallito", service)

    async def async_notify_match(self, match: Match, minutes: int) -> None:
        """Avviso "tra N minuti"."""
        time = dt_util.as_local(match.start).strftime("%H:%M")
        await self._send(
            self._texts()["soon"].format(minutes=minutes, match=self.describe(match), time=time)
        )

    async def async_test_notification(self) -> None:
        """Notifica di prova con la prossima partita."""
        texts = self._texts()
        match = self.next_match()
        if match is None:
            await self._send(texts["none"])
            return
        local = dt_util.as_local(match.start)
        await self._send(
            texts["next"].format(
                match=self.describe(match),
                date=local.strftime("%d/%m"),
                time=local.strftime("%H:%M"),
            )
        )

    # -------------------------------------------------------------- spettacolo
    @callback
    def async_start_show(self, play_song: bool = True, offset: float | None = None) -> None:
        """Avvia (o riavvia) lo spettacolo in background."""
        if self.show_running:
            self._show_task.cancel()  # type: ignore[union-attr]
        if offset is None:
            offset = float(self.options[CONF_SYNC_OFFSET])
        self._show_task = self.entry.async_create_background_task(
            self.hass, self._run_show(play_song, offset), "roma_roma_roma_show"
        )
        self._show_task.add_done_callback(lambda _task: self._signal())
        self.last_show = dt_util.utcnow()
        self._signal()

    async def async_stop_show(self) -> None:
        """Ferma lo spettacolo in corso."""
        if self.show_running:
            task = self._show_task
            task.cancel()  # type: ignore[union-attr]
            try:
                await task  # type: ignore[misc]
            except asyncio.CancelledError:
                pass
        self._show_task = None
        self._signal()

    async def _wait_available(self, entity_ids: list[str], timeout: float) -> None:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            if all(
                (s := self.hass.states.get(e)) is not None
                and s.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
                for e in entity_ids
            ):
                return
            await asyncio.sleep(0.5)
        _LOGGER.warning("Alcune luci non sono disponibili dopo %s s: continuo", timeout)

    async def _lights(
        self, entity_ids: list[str], brightness: int, color: tuple[int, int, int], blocking: bool
    ) -> None:
        if not entity_ids:
            return
        try:
            await self.hass.services.async_call(
                "light",
                "turn_on",
                {
                    "entity_id": entity_ids,
                    "brightness_pct": brightness,
                    "rgb_color": list(color),
                    "transition": LIGHT_TRANSITION,
                },
                blocking=blocking,
            )
        except Exception:  # noqa: BLE001 - una luce che non risponde non ferma lo show
            _LOGGER.debug("Comando luci fallito", exc_info=True)

    async def _play_song(self, players: list[str], song: str) -> None:
        """Avvia la canzone e attende che almeno un lettore suoni davvero."""
        started = asyncio.Event()

        @callback
        def _on_change(event: Event[EventStateChangedData]) -> None:
            new, old = event.data["new_state"], event.data["old_state"]
            if new is None or new.state != "playing":
                return
            if (
                old is None
                or old.state != "playing"
                or old.attributes.get("media_content_id") != new.attributes.get("media_content_id")
            ):
                started.set()

        unsub = async_track_state_change_event(self.hass, players, _on_change)
        try:
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": players,
                    "media_content_id": song,
                    "media_content_type": SONG_CONTENT_TYPE,
                },
                blocking=False,
            )
            try:
                async with asyncio.timeout(PLAYBACK_START_TIMEOUT):
                    await started.wait()
            except TimeoutError:
                _LOGGER.warning(
                    "La canzone non risulta partita entro %s s: avvio le luci comunque",
                    PLAYBACK_START_TIMEOUT,
                )
        finally:
            unsub()

    async def _run_show(self, play_song: bool, offset: float) -> None:
        opts = self.options
        red: list[str] = opts[CONF_RED_LIGHTS]
        yellow: list[str] = opts[CONF_YELLOW_LIGHTS]
        power: list[str] = opts[CONF_POWER_ENTITIES]
        players: list[str] = opts[CONF_MEDIA_PLAYERS]
        lo, hi = int(opts[CONF_MIN_BRIGHTNESS]), int(opts[CONF_MAX_BRIGHTNESS])

        if power:
            await self.hass.services.async_call(
                "homeassistant", "turn_on", {"entity_id": power}, blocking=True
            )
        if red or yellow:
            await self._wait_available(red + yellow, POWER_ON_TIMEOUT if power else 5)
            if power:
                await asyncio.sleep(2)
        await self._lights(red, hi, COLOR_RED, blocking=True)
        await self._lights(yellow, hi, COLOR_YELLOW, blocking=True)

        frames: list[Frame] = build_frames(self._beatmap.get("beats", []), lo, hi)
        if play_song and players:
            await self._play_song(players, opts[CONF_SONG])

        loop = asyncio.get_running_loop()
        t0 = loop.time() - offset
        for frame in frames:
            delay = t0 + frame.time - loop.time()
            if delay < -MAX_LATE_FRAME:
                continue
            if delay > 0:
                await asyncio.sleep(delay)
            await self._lights(red, frame.red, COLOR_RED, blocking=False)
            await self._lights(yellow, frame.yellow, COLOR_YELLOW, blocking=False)

        await asyncio.sleep(1)
        await self._lights(red, hi, COLOR_RED, blocking=False)
        await self._lights(yellow, hi, COLOR_YELLOW, blocking=False)

    # ------------------------------------------------------------------ utils
    @callback
    def _signal(self) -> None:
        async_dispatcher_send(self.hass, f"{SIGNAL_STATE_UPDATED}_{self.entry.entry_id}")
