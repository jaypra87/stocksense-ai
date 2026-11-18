"""Is every figure in an answer traceable to a tool result?

The model is told to use only numbers it fetched. This is the check behind
that instruction: pull the numbers out of the answer, pull the numbers out of
every tool result, and report what does not match. Small integers (counts,
horizons, "52-week") and the user's own figures are not worth flagging.
"""

import re
from collections.abc import Iterable

_NUMBER = re.compile(r"(?<![\w.])[-+]?\$?\d[\d,]*(?:\.\d+)?%?(?![\w.])")
_IGNORE_BELOW = 101  # bare integers up to 100 read as counts or ordinals
_YEARS = range(1990, 2101)
# How far a quoted figure may sit from a fetched one; the model is told to
# round, so $151.86 reported as $152 should pass and $160 should not.
_RELATIVE_TOLERANCE = 0.006


def numbers_in(text: str) -> list[tuple[str, float]]:
    found = []
    for match in _NUMBER.finditer(text):
        raw = match.group()
        try:
            value = float(raw.strip("$%+").replace(",", ""))
        except ValueError:
            continue
        found.append((raw, value))
    return found


def collect(payloads: Iterable[object]) -> set[float]:
    """Every number inside the tool results, plus the forms the model is
    likely to quote them in: rounded, and fractions as percentages."""
    out: set[float] = set()

    def walk(value: object) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, int | float):
            v = float(value)
            out.update({v, round(v), round(v, 1), round(v, 2)})
            if -1 <= v <= 1:
                out.update({v * 100, round(v * 100), round(v * 100, 1)})
            return
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list | tuple):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            for _, number in numbers_in(value):
                out.add(number)

    for payload in payloads:
        walk(payload)
    return out


def check(answer: str, payloads: Iterable[object], user_text: str = "") -> dict:
    grounded = collect(payloads)
    allowed = {value for _, value in numbers_in(user_text)}
    unmatched: list[str] = []
    checked = 0
    for raw, value in numbers_in(answer):
        bare = raw.strip("+-")
        if bare.isdigit() and (abs(value) < _IGNORE_BELOW or int(value) in _YEARS):
            continue
        checked += 1
        if value in allowed or _matches(abs(value), grounded):
            continue
        unmatched.append(raw)
    return {"checked": checked, "unmatched": unmatched}


def _matches(value: float, grounded: set[float]) -> bool:
    for g in grounded:
        g = abs(g)
        if g == value:
            return True
        scale = max(abs(g), 1.0)
        if abs(g - value) <= scale * _RELATIVE_TOLERANCE:
            return True
    return False
