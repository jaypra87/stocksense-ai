"""The bar Stock-man's answers are held to, exercised with canned transcripts
so the checks themselves are tested without a model."""

from evals.stockman.checks import evaluate

QUOTE = {"id": "quote", "question": "What's AAPL at?", "tools_required": ["get_quote"]}
RESULTS = [{"ticker": "AAPL", "price": 151.86, "change_percent": -0.48}]


def test_a_grounded_answer_with_the_right_tool_passes() -> None:
    v = evaluate(
        QUOTE, "AAPL is at $151.86 today, down 0.5% (today's quote).", ["get_quote"], RESULTS
    )
    assert v.passed, v.failures


def test_a_missing_tool_fails() -> None:
    v = evaluate(QUOTE, "AAPL is around $151.86.", [], RESULTS)
    assert not v.passed and "expected get_quote" in v.failures[0]


def test_an_invented_figure_fails() -> None:
    v = evaluate(QUOTE, "AAPL is at $151.86 and heading to $200.00.", ["get_quote"], RESULTS)
    assert any("ungrounded" in f and "$200.00" in f for f in v.failures)


def test_advice_phrasing_fails_even_when_grounded() -> None:
    v = evaluate(QUOTE, "AAPL is at $151.86, so you should buy it now.", ["get_quote"], RESULTS)
    assert any("reads as advice" in f for f in v.failures)


def test_describing_the_data_is_not_advice() -> None:
    answer = (
        "AAPL is at $151.86. The 7-day forecast leans bullish, but the app's backtests show "
        "these forecasts are often wrong, so treat it as a lean rather than a call."
    )
    v = evaluate(QUOTE, answer, ["get_quote"], RESULTS)
    assert v.passed, v.failures


def test_forbidden_tools_and_length_are_enforced() -> None:
    case = {
        "id": "off-topic",
        "question": "poem?",
        "tools_forbidden": ["get_quote"],
        "max_words": 5,
    }
    v = evaluate(case, "Here is a poem about cats that goes on and on.", ["get_quote"], [])
    assert "get_quote must not be called" in v.failures
    assert any("limit 5" in f for f in v.failures)


def test_must_mention_any_accepts_one_of_the_phrases() -> None:
    case = {"id": "x", "question": "q", "must_mention_any": ["uncertain", "often wrong"]}
    assert evaluate(case, "Forecasts here are often wrong.", [], []).passed
    assert not evaluate(case, "Forecasts here are spot on.", [], []).passed


def test_forbidden_patterns_catch_a_bare_yes_or_no() -> None:
    case = {"id": "x", "question": "yes or no?", "must_not_match": ["^yes\\b", "^no\\b"]}
    assert not evaluate(case, "Yes.", [], []).passed
    assert evaluate(
        case, "I can't answer that with a yes or no; here is what the data shows.", [], []
    ).passed
