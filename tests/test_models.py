import json
from decimal import Decimal

import pytest

from saucebot.models import (BotError, Product, Totals, check_totals, load_order,
                             parse_price, split_found_missing)

CATALOG = [Product("Sauce Labs Backpack", "d", Decimal("29.99")),
           Product("Sauce Labs Onesie", "d", Decimal("7.99"))]


def test_parse_price():
    assert parse_price("$29.99") == Decimal("29.99")
    assert parse_price("Item total: $1,037.50") == Decimal("1037.50")
    with pytest.raises(BotError):
        parse_price("free")


def test_missing_items_are_reported_not_guessed():
    found, missing = split_found_missing(
        ["Sauce Labs Backpack", "Sauce Labs Water Bottle", "sauce labs onesie"], CATALOG)
    assert [p.name for p in found] == ["Sauce Labs Backpack"]
    assert missing == ["Sauce Labs Water Bottle", "sauce labs onesie"]


def test_totals_ok_and_mismatch():
    found = CATALOG
    check_totals(found, Totals(Decimal("37.98"), Decimal("3.04"), Decimal("41.02")))
    with pytest.raises(BotError, match="Item total mismatch"):
        check_totals(found, Totals(Decimal("40.00"), Decimal("3.20"), Decimal("43.20")))
    with pytest.raises(BotError, match="Total mismatch"):
        check_totals(found, Totals(Decimal("37.98"), Decimal("3.04"), Decimal("50.00")))


def test_load_order_dedupes_and_validates(tmp_path):
    f = tmp_path / "in.json"
    f.write_text(json.dumps({"items": ["a", "a", "b"],
                             "customer": {"first_name": "A", "last_name": "B", "zip": "1"}}))
    assert load_order(f).items == ["a", "b"]
    f.write_text("{}")
    with pytest.raises(BotError):
        load_order(f)
