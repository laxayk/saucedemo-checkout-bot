"""Plain data types and the pure logic that needs no browser (easy to unit test)."""
import json
import re
from dataclasses import dataclass, field, asdict
from decimal import Decimal
from pathlib import Path
from typing import Optional


class BotError(Exception):
    """A run-level failure with a message that is safe to put in result.json."""


@dataclass(frozen=True)
class Product:
    name: str
    description: str
    price: Decimal


@dataclass(frozen=True)
class Customer:
    first_name: str
    last_name: str
    zip: str


@dataclass(frozen=True)
class Order:
    items: list
    customer: Customer


@dataclass
class Totals:
    item_total: Decimal
    tax: Decimal
    total: Decimal


@dataclass
class Result:
    status: str = "failed"
    requested_items: list = field(default_factory=list)
    ordered_items: list = field(default_factory=list)
    missing_items: list = field(default_factory=list)
    totals: Optional[Totals] = None
    confirmation_message: Optional[str] = None
    error: Optional[str] = None

    def to_json(self) -> str:
        def default(o):
            if isinstance(o, Decimal):
                return float(o)
            raise TypeError(type(o))

        return json.dumps(asdict(self), indent=2, default=default)


def parse_price(text: str) -> Decimal:
    """'$29.99' -> Decimal('29.99'). Also accepts 'Item total: $39.98'."""
    match = re.search(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)", text)
    if not match:
        raise BotError(f"Could not read a price from {text!r}")
    return Decimal(match.group(1).replace(",", ""))


def load_order(path: Path) -> Order:
    try:
        data = json.loads(Path(path).read_text())
        customer = Customer(**{k: str(data["customer"][k]) for k in ("first_name", "last_name", "zip")})
        items = data["items"]
        if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
            raise ValueError("'items' must be a list of strings")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise BotError(f"Invalid input file {path}: {exc!r}") from exc
    return Order(items=_dedupe(items), customer=customer)


def _dedupe(items: list) -> list:
    """Drop repeated names (keep order). The store sells one of each per cart."""
    seen, out = set(), []
    for name in items:
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def split_found_missing(requested: list, catalog: list):
    """Exact name match only. Anything not in the catalog is reported, never guessed."""
    by_name = {p.name: p for p in catalog}
    found = [by_name[n] for n in requested if n in by_name]
    missing = [n for n in requested if n not in by_name]
    return found, missing


def check_totals(found: list, totals: Totals) -> None:
    """Fail loudly if the shop's numbers disagree with the prices we collected."""
    expected = sum((p.price for p in found), Decimal("0"))
    if totals.item_total != expected:
        raise BotError(
            f"Item total mismatch: page shows {totals.item_total}, collected prices sum to {expected}"
        )
    if totals.item_total + totals.tax != totals.total:
        raise BotError(
            f"Total mismatch: item total {totals.item_total} + tax {totals.tax} != total {totals.total}"
        )
