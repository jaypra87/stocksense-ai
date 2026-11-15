"""Publishers put " -- " between headline clauses; the UI shows a colon instead."""

from app.services.market_data.base import NewsItemDTO, tidy_headline


def test_double_hyphen_clause_becomes_a_colon() -> None:
    assert (
        tidy_headline("Forget Former Nvidia CEO Jensen Huang -- This Is the Real Question")
        == "Forget Former Nvidia CEO Jensen Huang: This Is the Real Question"
    )


def test_em_and_en_dash_clauses_too() -> None:
    assert tidy_headline("Stocks rise — bonds fall") == "Stocks rise: bonds fall"
    assert tidy_headline("Stocks rise – bonds fall") == "Stocks rise: bonds fall"


def test_a_pair_of_dashes_is_an_aside_and_becomes_commas() -> None:
    assert (
        tidy_headline("Nvidia earnings -- along with the baggage -- top next week's markets")
        == "Nvidia earnings, along with the baggage, top next week's markets"
    )


def test_hyphens_inside_words_and_numbers_are_kept() -> None:
    assert tidy_headline("BRK-B gains as 10-year yield dips to -0.5%") == (
        "BRK-B gains as 10-year yield dips to -0.5%"
    )


def test_dto_applies_it_to_title_and_summary() -> None:
    item = NewsItemDTO(title="  A -- B  ", summary="C — D")
    assert item.title == "A: B"
    assert item.summary == "C: D"
