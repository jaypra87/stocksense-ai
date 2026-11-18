"""Is every figure in an answer traceable to a tool result?

The model is told to use only numbers it fetched. This is the check behind
that instruction: pull the numbers out of the answer, pull the numbers out of
every tool result, and report what does not match. Small integers (counts,
horizons, "52-week") and the user's own figures are not worth flagging.
"""

import re
from collections.abc import Iterable

# Thousands separators only between digit groups, so "November 18, 2026"
# yields 18 and 2026, not "18,". A trailing period is sentence punctuation.
_NUMBER = re.compile(r"(?<![\w.])[-+]?\$?\d+(?:,\d{3})*(?:\.\d+)?%?(?!\w|\.\d)")
_IGNORE_BELOW = 101  # bare integers up to 100 read as counts or ordinals
_YEARS = range(1990, 2101)
# How far a quoted figure may sit from a fetched one; the model is told to
# round, so $151.86 reported as $152 should pass and $160 should not.
_RELATIVE_TOLERANCE = 0.006
# Numbers per tool result that take part in pairing; results are trimmed, so
# this is a guard, not a budget.
_MAX_PAIRED = 80


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
    for v in _raw_numbers(payloads):
        out.update({v, round(v), round(v, 1), round(v, 2)})
        if -1 <= v <= 1:
            out.update({v * 100, round(v * 100), round(v * 100, 1)})
    return out


def _raw_numbers(payloads: Iterable[object]) -> set[float]:
    out: set[float] = set()

    def walk(value: object) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, int | float):
            out.add(float(value))
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
    payloads = list(payloads)
    grounded = collect(payloads)
    derived: set[float] | None = None
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
        if derived is None:
            derived = _derived(payloads)
        if _matches_derived(raw, abs(value), derived):
            continue
        unmatched.append(raw)
    return {"checked": checked, "unmatched": unmatched}


def _derived(payloads: Iterable[object]) -> set[float]:
    """Figures the model may work out from two numbers in the same tool
    result: their difference, and the percent change between them ("1.2%
    below its 52-week high"). Computed once per check; pairs are taken within
    one result only, so unrelated numbers do not combine into coincidences."""
    out: set[float] = set()
    for payload in payloads:
        values = [v for v in _raw_numbers([payload]) if v != 0][:_MAX_PAIRED]
        for i, a in enumerate(values):
            for b in values[i + 1 :]:
                diff = abs(a - b)
                out.add(diff)
                out.add(diff / abs(b) * 100)
                out.add(diff / abs(a) * 100)
    return out


def _matches_derived(raw: str, value: float, derived: set[float]) -> bool:
    """Exact after rounding to the precision the model wrote, not a tolerance:
    a derived candidate has to land on the quoted figure."""
    digits = raw.split(".")[1].rstrip("%") if "." in raw else ""
    places = len(digits)
    return any(round(c, places) == value for c in derived)


def _matches(value: float, grounded: set[float]) -> bool:
    for g in grounded:
        g = abs(g)
        if g == value:
            return True
        scale = max(abs(g), 1.0)
        if abs(g - value) <= scale * _RELATIVE_TOLERANCE:
            return True
    return False
