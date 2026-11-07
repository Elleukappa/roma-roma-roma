"""Parser minimale del calendario ICS delle partite (senza dipendenze esterne)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import re
from zoneinfo import ZoneInfo

TEAM_MARKERS = ("AS Roma", "Roma")
_TAG_RE = re.compile(r"\[([A-Za-z0-9 ]{1,12})\]")
_SCORE_RE = re.compile(r"\((\d+)\s*-\s*(\d+)\)\s*$")
DEFAULT_DURATION = timedelta(minutes=105)


@dataclass(frozen=True, slots=True)
class Match:
    """Una partita (o evento) della squadra."""

    uid: str
    summary: str
    start: datetime
    end: datetime
    location: str | None
    competition: str | None  # es. "CL", "EL", "CI"; None = campionato
    home: bool
    opponent: str
    score: str | None  # "2-1" se già giocata

    @property
    def is_league(self) -> bool:
        """True se è una partita di campionato (nessuna etichetta di coppa)."""
        return self.competition is None

    @property
    def title(self) -> str:
        """Titolo pulito, senza etichette e risultato."""
        text = _SCORE_RE.sub("", _TAG_RE.sub("", self.summary))
        return " ".join(text.split())


def _unfold(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        elif raw:
            lines.append(raw)
    return lines


def _unescape(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def _parse_dt(value: str, params: dict[str, str], default_tz: timezone | ZoneInfo) -> datetime:
    value = value.strip()
    if params.get("VALUE") == "DATE" or (len(value) == 8 and value.isdigit()):
        d = date(int(value[0:4]), int(value[4:6]), int(value[6:8]))
        return datetime(d.year, d.month, d.day, tzinfo=default_tz).astimezone(timezone.utc)
    utc = value.endswith("Z")
    value = value.rstrip("Z")
    dt = datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    if utc:
        return dt.replace(tzinfo=timezone.utc)
    tzid = params.get("TZID")
    tz: timezone | ZoneInfo = default_tz
    if tzid:
        try:
            tz = ZoneInfo(tzid)
        except Exception:  # noqa: BLE001 - TZID sconosciuto: si usa il fuso di default
            tz = default_tz
    return dt.replace(tzinfo=tz).astimezone(timezone.utc)


def _split_prop(line: str) -> tuple[str, dict[str, str], str]:
    head, _, value = line.partition(":")
    parts = head.split(";")
    params: dict[str, str] = {}
    for part in parts[1:]:
        key, _, val = part.partition("=")
        params[key.upper()] = val.strip('"')
    return parts[0].upper(), params, value


def _describe(summary: str) -> tuple[str | None, bool, str, str | None]:
    tag_match = _TAG_RE.search(summary)
    competition = tag_match.group(1).strip().upper() if tag_match else None
    score_match = _SCORE_RE.search(summary)
    score = f"{score_match.group(1)}-{score_match.group(2)}" if score_match else None
    clean = " ".join(_SCORE_RE.sub("", _TAG_RE.sub("", summary)).split())
    home_team, sep, away_team = clean.partition(" - ")
    if not sep:
        return competition, True, clean, score
    home = any(m.lower() == home_team.strip().lower() for m in TEAM_MARKERS)
    opponent = away_team.strip() if home else home_team.strip()
    return competition, home, opponent, score


def parse_ics(text: str, default_tz: timezone | ZoneInfo = timezone.utc) -> list[Match]:
    """Converte il testo ICS in una lista di partite ordinata per data."""
    matches: list[Match] = []
    current: dict[str, tuple[dict[str, str], str]] | None = None
    for line in _unfold(text):
        upper = line.upper()
        if upper == "BEGIN:VEVENT":
            current = {}
            continue
        if upper == "END:VEVENT":
            if current is not None:
                match = _build(current, default_tz)
                if match is not None:
                    matches.append(match)
            current = None
            continue
        if current is None:
            continue
        name, params, value = _split_prop(line)
        if name not in current:
            current[name] = (params, value)
    matches.sort(key=lambda m: m.start)
    return matches


def _build(
    props: dict[str, tuple[dict[str, str], str]], default_tz: timezone | ZoneInfo
) -> Match | None:
    if "DTSTART" not in props or "SUMMARY" not in props:
        return None
    status = props.get("STATUS", ({}, ""))[1].strip().upper()
    if status == "CANCELLED":
        return None
    try:
        start = _parse_dt(props["DTSTART"][1], props["DTSTART"][0], default_tz)
        end = (
            _parse_dt(props["DTEND"][1], props["DTEND"][0], default_tz)
            if "DTEND" in props
            else start + DEFAULT_DURATION
        )
    except ValueError:
        return None
    if end <= start:
        end = start + DEFAULT_DURATION
    summary = _unescape(props["SUMMARY"][1]).strip()
    location = _unescape(props["LOCATION"][1]).strip() if "LOCATION" in props else None
    competition, home, opponent, score = _describe(summary)
    uid = props.get("UID", ({}, f"{start.isoformat()}-{summary}"))[1].strip()
    return Match(
        uid=uid,
        summary=summary,
        start=start,
        end=end,
        location=location or None,
        competition=competition,
        home=home,
        opponent=opponent,
        score=score,
    )
