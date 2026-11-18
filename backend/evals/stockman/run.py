"""Run Stock-man's eval set against the real model.

    cd backend && source .venv/bin/activate
    python -m evals.stockman.run            # all cases
    python -m evals.stockman.run risk quote # a subset

Uses the fake market-data provider, so the numbers are deterministic and the
only variable is the model. Each case is one turn in a fresh conversation for
a throwaway guest. Costs a few cents on Haiku; needs ANTHROPIC_API_KEY.
Writes a JSON report next to this file and exits non-zero on any failure.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

from app.api.v1.stockman import get_anthropic_client
from app.core.config import get_settings
from app.db.models.user import User
from app.db.session import SessionLocal, set_rls_user, system_session
from app.services.market_data.fake_provider import FakeProvider
from app.services.stockman import agent
from app.services.stockman.tools import ToolContext
from evals.stockman.checks import Verdict, evaluate
from tests.conftest import InMemoryRedis

HERE = Path(__file__).parent
CASES = json.loads((HERE / "cases.json").read_text())


def run_case(case: dict, client, user_id) -> tuple[Verdict, dict]:
    db = SessionLocal()
    set_rls_user(db, user_id)
    ctx = ToolContext(db=db, redis=InMemoryRedis(), provider=FakeProvider(), user_id=user_id)
    calls: list[str] = []
    done: dict = {}
    started = time.perf_counter()
    try:
        for name, data in agent.run_turn(client, ctx, [], case["question"]):
            if name == "tool_call":
                calls.append(data["name"])
            elif name == "done":
                done = data
    finally:
        db.close()
    results = _tool_payloads(done.get("transcript", []))
    verdict = evaluate(case, done.get("answer", ""), calls, results)
    return verdict, {
        "answer": done.get("answer", ""),
        "usage": done.get("usage"),
        "rounds": done.get("rounds"),
        "seconds": round(time.perf_counter() - started, 1),
    }


def _tool_payloads(transcript: list[dict]) -> list[object]:
    out: list[object] = []
    for turn in transcript:
        if turn["role"] != "user":
            continue
        for block in turn["content"]:
            if block.get("type") == "tool_result" and not block.get("is_error"):
                try:
                    out.append(json.loads(block["content"]))
                except (TypeError, ValueError):
                    out.append(block["content"])
    return out


def main(argv: list[str]) -> int:
    # Show the retries and tool failures as they happen.
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logging.getLogger("app.services.stockman").setLevel(logging.INFO)
    settings = get_settings()
    if not settings.stockman_enabled:
        print("ANTHROPIC_API_KEY is not set; nothing to run.")
        return 2
    wanted = set(argv) or {c["id"] for c in CASES}
    cases = [c for c in CASES if c["id"] in wanted]

    db = system_session()
    user = User(is_guest=True)
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()

    client = get_anthropic_client()
    report = {"model": settings.stockman_model, "cases": []}
    passed = 0
    try:
        for case in cases:
            try:
                verdict, extra = run_case(case, client, user_id)
            except Exception as exc:  # noqa: BLE001 - one broken case must not end the run
                verdict = Verdict(case_id=case["id"], passed=False, failures=[f"crashed: {exc}"])
                extra = {"answer": "", "usage": None, "rounds": None, "seconds": None}
            passed += verdict.passed
            mark = "PASS" if verdict.passed else "FAIL"
            print(
                f"{mark} {case['id']:18} tools={','.join(verdict.tools) or '-'} "
                f"words={verdict.words} {extra['seconds']}s"
            )
            for failure in verdict.failures:
                print(f"       {failure}")
            report["cases"].append({**vars(verdict), **extra})
    finally:
        db = system_session()
        db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
        db.commit()
        db.close()

    report["passed"], report["total"] = passed, len(cases)
    (HERE / "last_report.json").write_text(json.dumps(report, indent=2, default=str))
    tokens = sum(
        (c["usage"] or {}).get("input_tokens", 0) + (c["usage"] or {}).get("output_tokens", 0)
        for c in report["cases"]
    )
    print(f"\n{passed}/{len(cases)} passed on {settings.stockman_model}, {tokens} tokens")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    code = main(sys.argv[1:])
    # Skip interpreter teardown: on an Intel Python under Rosetta a native
    # finalizer in the SDK's JSON parser can hang the exit for minutes. The
    # report is on disk and stdout is flushed, so nothing is lost.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
