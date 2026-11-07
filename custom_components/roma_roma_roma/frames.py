"""Calcolo dei "fotogrammi" dello spettacolo di luci (logica pura, testabile)."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

BEATMAP_FILE = Path(__file__).parent / "beatmap.json"
STRONG_PERCENTILE = 0.88


@dataclass(frozen=True, slots=True)
class Frame:
    """Luminosità (in %) delle luci rosse e gialle a un dato istante della canzone."""

    time: float
    red: int
    yellow: int


def load_beatmap(path: Path = BEATMAP_FILE) -> dict:
    """Carica la mappa delle battute precalcolata sulla canzone."""
    return json.loads(path.read_text(encoding="utf-8"))


def _percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[int(p * (len(ordered) - 1))]


def build_frames(beats: list[list[float]], min_pct: int, max_pct: int) -> list[Frame]:
    """Una battuta = un fotogramma.

    A ogni battuta le luci si alternano: chi "guida" sale in base a bassi e volume,
    l'altra resta soffusa (più o meno in base al volume). Sui colpi più forti dei
    ritornelli si accendono entrambe al massimo.
    """
    lo = max(1, min(100, int(min_pct)))
    hi = max(lo, min(100, int(max_pct)))
    span = hi - lo
    strong = _percentile([b[1] for b in beats], STRONG_PERCENTILE) if beats else 1.0
    frames: list[Frame] = []
    for index, (time, bass, loud) in enumerate(beats):
        lead = lo + span * (0.45 * loud + 0.55 * bass)
        other = lo + span * 0.25 * loud
        if bass >= strong and loud > 0.5:
            lead = other = hi
        lead_i = _round5(lead, lo, hi)
        other_i = _round5(other, lo, hi)
        if index % 2 == 0:
            frames.append(Frame(time, lead_i, other_i))
        else:
            frames.append(Frame(time, other_i, lead_i))
    return frames


def _round5(value: float, lo: int, hi: int) -> int:
    return int(max(lo, min(hi, round(value / 5) * 5)))
