"""Live end-to-end tests against saucedemo.com (skipped with SKIP_E2E=1)."""
import json
import os
from pathlib import Path

import pytest

from saucebot.bot import run
from saucebot.config import Config

pytestmark = pytest.mark.skipif(os.environ.get("SKIP_E2E") == "1", reason="live site")
PASSWORD = os.environ.get("SAUCE_PASSWORD", "secret_sauce")  # public demo password
INPUT = Path(__file__).parent.parent / "input.json"


@pytest.mark.parametrize("user", ["standard_user", "performance_glitch_user"])
def test_full_run(user, tmp_path):
    cfg = Config(username=user, password=PASSWORD)
    result = run(cfg, INPUT, tmp_path)
    data = json.loads((tmp_path / "result.json").read_text())
    assert data["status"] == "success", data
    assert data["missing_items"] == ["Sauce Labs Water Bottle"]
    assert data["totals"] == {"item_total": 37.98, "tax": 3.04, "total": 41.02}
    assert (tmp_path / "confirmation.png").exists()
    assert len(json.loads((tmp_path / "products.json").read_text())) == 6


def test_locked_out_user_fails_clearly(tmp_path):
    result = run(Config(username="locked_out_user", password=PASSWORD), INPUT, tmp_path)
    data = json.loads((tmp_path / "result.json").read_text())
    assert data["status"] == "failed" and "locked out" in data["error"]


def test_all_items_missing_fails_without_checkout(tmp_path):
    f = tmp_path / "in.json"
    f.write_text(json.dumps({"items": ["Nope"], "customer": {"first_name": "A", "last_name": "B", "zip": "1"}}))
    run(Config(username="standard_user", password=PASSWORD), f, tmp_path)
    data = json.loads((tmp_path / "result.json").read_text())
    assert data["status"] == "failed" and data["missing_items"] == ["Nope"]
    assert not (tmp_path / "confirmation.png").exists()


def test_bad_input_file_is_reported(tmp_path):
    f = tmp_path / "in.json"
    f.write_text("{not json")
    run(Config(username="standard_user", password=PASSWORD), f, tmp_path)
    data = json.loads((tmp_path / "result.json").read_text())
    assert data["status"] == "failed" and "Invalid input file" in data["error"]
