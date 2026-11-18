"""The tool loop behind one Stock-man turn.

`run_turn` is a generator of (event, data) pairs the router forwards as
server-sent events: text as it streams, each tool call and its result, and a
final `done` carrying everything the router needs to persist. The loop is
written by hand rather than with the SDK's tool runner because the UI wants
per-token text and per-tool progress, and the final round must be forced to
answer without tools.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import anthropic
    from anthropic.types import MessageParam, ToolParam

from app.core.config import get_settings
from app.services.stockman import grounding, tools
from app.services.stockman.prompts import GROUNDING_NUDGE, REFUSED, SYSTEM_PROMPT
from app.services.stockman.tools import ToolContext, ToolError

logger = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 2048
Event = tuple[str, dict[str, Any]]


def run_turn(
    client: anthropic.Anthropic,
    ctx: ToolContext,
    history: list[dict],
    user_text: str,
) -> Iterator[Event]:
    settings = get_settings()
    messages: list[dict] = [*history, {"role": "user", "content": user_text}]
    # Turns to persist, in order. The user turn is saved by the caller before
    # streaming starts; a superseded answer never reaches this list.
    transcript: list[dict] = []
    results_seen: list[object] = []
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}
    retried = False
    rounds = 0
    answer = ""

    while True:
        rounds += 1
        last_round = rounds >= settings.stockman_max_tool_rounds
        text_parts: list[str] = []
        with client.messages.stream(
            model=settings.stockman_model,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=cast("list[ToolParam]", tools.TOOL_DEFINITIONS),
            tool_choice={"type": "none"} if last_round else {"type": "auto"},
            output_config={"effort": "medium"},
            messages=cast("list[MessageParam]", messages),
        ) as stream:
            for event in stream:
                if event.type == "text":
                    text_parts.append(event.text)
                    yield "text_delta", {"text": event.text}
            message = stream.get_final_message()

        usage["input_tokens"] += message.usage.input_tokens
        usage["output_tokens"] += message.usage.output_tokens
        # Reported, not estimated: a zero here across turns means the cached
        # prefix (system prompt + tools) is being invalidated somewhere.
        usage["cache_read_input_tokens"] += (
            getattr(message.usage, "cache_read_input_tokens", 0) or 0
        )
        blocks = [b.model_dump(mode="json", exclude_none=True) for b in message.content]
        answer = "".join(text_parts)

        if message.stop_reason == "refusal":
            yield "text_reset", {}
            yield "text_delta", {"text": REFUSED}
            answer = REFUSED
            transcript.append({"role": "assistant", "content": [{"type": "text", "text": REFUSED}]})
            break

        tool_uses = [b for b in message.content if b.type == "tool_use"]
        if message.stop_reason == "max_tokens" and tool_uses:
            # A truncated tool input parses as a plausible partial; never run it.
            logger.warning("stockman: tool input truncated at max_tokens")
            tool_uses = []

        transcript.append({"role": "assistant", "content": blocks})
        messages.append({"role": "assistant", "content": blocks})

        if tool_uses:
            results = []
            for use in tool_uses:
                yield "tool_call", {"id": use.id, "name": use.name, "input": use.input}
                try:
                    args = use.input if isinstance(use.input, dict) else {}
                    payload = tools.run(ctx, use.name, args)
                    content, is_error = json.dumps(payload, default=str), False
                    results_seen.append(payload)
                except ToolError as exc:
                    content, is_error = str(exc), True
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": use.id,
                        "content": content,
                        "is_error": is_error,
                    }
                )
                yield "tool_result", {"id": use.id, "name": use.name, "ok": not is_error}
            transcript.append({"role": "user", "content": results})
            messages.append({"role": "user", "content": results})
            continue

        check = grounding.check(answer, results_seen, user_text)
        if check["unmatched"] and not retried:
            retried = True
            logger.info("stockman: ungrounded figures %s, retrying", check["unmatched"])
            transcript.pop()
            messages.append(
                {
                    "role": "system",
                    "content": GROUNDING_NUDGE.format(figures=", ".join(check["unmatched"])),
                }
            )
            yield "text_reset", {}
            continue
        break

    yield (
        "done",
        {
            "answer": answer,
            "transcript": transcript,
            "usage": usage,
            "grounding": grounding.check(answer, results_seen, user_text),
            "rounds": rounds,
        },
    )
