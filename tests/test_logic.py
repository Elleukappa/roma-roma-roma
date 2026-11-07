"""Test della logica pura (parser ICS e fotogrammi) senza Home Assistant."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "custom_components" / "roma_roma_roma"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"rrr_{name}", PKG / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ics = _load("ics")
frames = _load("frames")


def _matches():
    text = (ROOT / "tests" / "fixtures" / "as-roma.ics").read_text(encoding="utf-8")
    return ics.parse_ics(text)


def test_parse_basic_fields():
    matches = _matches()
    assert [m.uid for m in matches] == ["past-1@maak-agenda.nl", "next-1@maak-agenda.nl", "tz-1@maak-agenda.nl", "cup-1@maak-agenda.nl"]
    past, nxt, tz, cup = matches
    assert past.competition == "CL" and past.score == "3-2" and not past.home
    assert past.opponent == "Manchester United" and past.title == "Manchester United - AS Roma"
    assert nxt.start == datetime(2026, 11, 7, 19, 45, tzinfo=timezone.utc)
    assert nxt.home and nxt.opponent == "US Sassuolo" and nxt.is_league and nxt.location == "Olimpico"
    assert cup.competition == "CL" and not cup.is_league


def test_tzid_and_default_duration():
    tz = _matches()[2]
    # 18:00 ora di Roma (CET) = 17:00 UTC
    assert tz.start == datetime(2026, 11, 21, 17, 0, tzinfo=timezone.utc)
    assert tz.end - tz.start == timedelta(minutes=105)
    assert tz.opponent == "Parma" and not tz.home


def test_cancelled_skipped():
    assert all("Test" not in m.summary for m in _matches())


def test_real_beatmap_frames():
    beatmap = frames.load_beatmap()
    assert len(beatmap["beats"]) == 244
    fr = frames.build_frames(beatmap["beats"], 10, 100)
    assert len(fr) == 244
    assert all(10 <= f.red <= 100 and 10 <= f.yellow <= 100 for f in fr)
    times = [f.time for f in fr]
    assert times == sorted(times) and times[-1] < beatmap["duration"]
    # alternanza: nelle battute pari guida il rosso, nelle dispari il giallo
    assert sum(f.red >= f.yellow for f in fr[0::2]) == len(fr[0::2])
    assert sum(f.yellow >= f.red for f in fr[1::2]) == len(fr[1::2])
    # qualche flash con entrambe al massimo nei ritornelli
    assert 10 <= sum(f.red == f.yellow == 100 for f in fr) <= 60


def test_brightness_range_respected():
    fr = frames.build_frames(frames.load_beatmap()["beats"], 30, 60)
    assert all(30 <= f.red <= 60 and 30 <= f.yellow <= 60 for f in fr)
