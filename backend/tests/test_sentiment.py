from app.services.market_data.fake_provider import FakeProvider
from app.services.sentiment import analyze, label_from_score, score_text


def test_positive_headline_scores_positive() -> None:
    s = score_text("Company beats earnings as revenue surges to record high")
    assert s > 0
    assert label_from_score(s) == "positive"


def test_negative_headline_scores_negative() -> None:
    s = score_text("Stock plunges after company misses targets amid lawsuit")
    assert s < 0
    assert label_from_score(s) == "negative"


def test_neutral_headline() -> None:
    assert label_from_score(score_text("Company to report earnings next week")) == "neutral"


def test_negation_flips_sentiment() -> None:
    # "not strong" should not be read as positive.
    assert score_text("Company is not strong") <= 0


def test_analyze_aggregates_counts_and_overall() -> None:
    titles = [
        "Revenue surges, shares rally to record high",  # positive
        "Stock plunges on weak guidance and losses",  # negative
        "Company to host investor day next month",  # neutral
    ]
    result = analyze(titles)
    assert result["counts"]["positive"] == 1
    assert result["counts"]["negative"] == 1
    assert -1 <= result["overall_score"] <= 1
    assert result["overall_label"] in {"positive", "negative", "neutral", "mixed"}


def test_fake_provider_news_is_deterministic() -> None:
    a = FakeProvider().get_news("AAPL")
    b = FakeProvider().get_news("AAPL")
    assert [n.title for n in a] == [n.title for n in b]
    assert len(a) > 0
