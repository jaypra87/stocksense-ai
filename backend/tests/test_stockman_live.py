"""Stock-man against the real model. Opt in with `pytest -m live`; it spends a
few cents and needs ANTHROPIC_API_KEY. The same cases as evals/stockman."""

import pytest

from app.core.config import get_settings
from evals.stockman import run as eval_run

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not get_settings().stockman_enabled, reason="ANTHROPIC_API_KEY not set"),
]


@pytest.mark.parametrize("case", eval_run.CASES, ids=[c["id"] for c in eval_run.CASES])
def test_case(case: dict, live_user) -> None:
    verdict, extra = eval_run.run_case(case, eval_run.get_anthropic_client(), live_user)
    assert verdict.passed, f"{verdict.failures}\n--- answer ---\n{extra['answer']}"


@pytest.fixture(scope="module")
def live_user():
    from app.db.models.user import User
    from app.db.session import system_session

    db = system_session()
    user = User(is_guest=True)
    db.add(user)
    db.commit()
    uid = user.id
    db.close()
    yield uid
    db = system_session()
    db.query(User).filter(User.id == uid).delete(synchronize_session=False)
    db.commit()
    db.close()
