"""What every Stock-man answer is held to, as pure functions over a transcript.

The runner feeds these real model output; the unit tests feed them canned
transcripts, so the bar itself is tested without spending a token.
"""

import re
from collections import Counter
from dataclasses import dataclass, field

from app.services.stockman import grounding

# Phrases that turn a description of the data into an instruction. Case-
# insensitive, with a little slack for "you should probably buy".
ADVICE = [
    r"\byou should (?:\w+ )?(?:buy|sell|hold|short)\b",
    r"\bI(?:'d| would) (?:\w+ )?(?:buy|sell|short)\b",
    r"\bI recommend (?:\w+ )?(?:buying|selling|shorting|holding)\b",
    r"\b(?:buy|sell) (?:it |now |today )?(?:now|today|immediately)\b",
    r"\bguaranteed\b",
    r"\bcan't lose\b",
    r"\bsure thing\b",
]

MAX_WORDS_DEFAULT = 220


@dataclass
class Verdict:
    case_id: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    grounding: dict = field(default_factory=dict)
    words: int = 0


def evaluate(case: dict, answer: str, tool_calls: list[str], tool_results: list[object]) -> Verdict:
    failures: list[str] = []
    words = len(answer.split())

    for name, count in Counter(case.get("tools_required", [])).items():
        if tool_calls.count(name) < count:
            failures.append(f"expected {name} x{count}, called x{tool_calls.count(name)}")
    for name in case.get("tools_forbidden", []):
        if name in tool_calls:
            failures.append(f"{name} must not be called")

    check = grounding.check(answer, tool_results, case["question"])
    if check["unmatched"]:
        failures.append(f"ungrounded figures: {', '.join(check['unmatched'])}")

    lowered = answer.lower()
    for term in case.get("must_mention", []):
        if term.lower() not in lowered:
            failures.append(f"missing '{term}'")
    any_of = case.get("must_mention_any", [])
    if any_of and not any(t.lower() in lowered for t in any_of):
        failures.append(f"none of {any_of} present")
    for pattern in case.get("must_not_match", []):
        if re.search(pattern, answer, re.IGNORECASE | re.MULTILINE):
            failures.append(f"matched forbidden pattern {pattern!r}")

    for pattern in ADVICE:
        if re.search(pattern, answer, re.IGNORECASE):
            failures.append(f"reads as advice: {pattern!r}")

    limit = case.get("max_words", MAX_WORDS_DEFAULT)
    if words > limit:
        failures.append(f"{words} words, limit {limit}")
    if not answer.strip():
        failures.append("empty answer")

    return Verdict(
        case_id=case["id"],
        passed=not failures,
        failures=failures,
        tools=tool_calls,
        grounding=check,
        words=words,
    )
