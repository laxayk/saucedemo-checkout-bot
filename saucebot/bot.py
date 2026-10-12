"""The end-to-end flow. Each step is one short function so the run reads top to bottom."""
import json
import logging
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from .config import Config
from .models import BotError, Result, check_totals, load_order, split_found_missing
from .pages import CartPage, CheckoutPage, InventoryPage, LoginPage

log = logging.getLogger("saucebot")


def run(config: Config, input_path: Path, out_dir: Path) -> Result:
    """Run the whole flow. Always writes result.json, even when the run fails."""
    out_dir.mkdir(parents=True, exist_ok=True)
    result = Result()
    page = None
    try:
        order = load_order(input_path)
        result.requested_items = list(order.items)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=config.headless, slow_mo=config.slow_mo_ms)
            context_args = {"viewport": {"width": 1280, "height": 720}}
            if config.video_dir:
                context_args.update(record_video_dir=config.video_dir, record_video_size={"width": 1280, "height": 720})
            context = browser.new_context(**context_args)
            page = context.new_page()
            page.set_default_timeout(config.timeout_ms)
            page.set_default_navigation_timeout(config.timeout_ms)
            try:
                _flow(page, config, order, out_dir, result)
            except PWTimeout as exc:
                raise BotError("Timed out waiting for the page: " + str(exc).splitlines()[0]) from exc
            finally:
                if result.status != "success":
                    _save_failure_screenshot(page, out_dir)
                context.close()  # flushes the demo video, if any
                browser.close()
    except BotError as exc:
        result.status, result.error = "failed", str(exc)
        log.error("Run failed: %s", exc)
    except Exception as exc:  # unexpected: still report it, never hide it
        result.status, result.error = "failed", f"Unexpected {type(exc).__name__}: {exc}"
        log.exception("Unexpected error")
    (out_dir / "result.json").write_text(result.to_json() + "\n")
    return result


def _flow(page, config, order, out_dir: Path, result: Result) -> None:
    log.info("Logging in as %s", config.username)
    LoginPage(page, config.base_url).login(config.username, config.password)

    inventory = InventoryPage(page)
    catalog = inventory.collect_products()
    _write_products(catalog, out_dir)
    log.info("Collected %d products", len(catalog))

    found, missing = split_found_missing(order.items, catalog)
    result.missing_items = missing
    if missing:
        log.warning("Not in catalog, skipping: %s", missing)
    if not found:
        raise BotError("None of the requested items exist in the store; nothing to check out")

    for product in found:
        inventory.add_to_cart(product.name)
    expected_names = [p.name for p in found]

    cart = CartPage(page, config.base_url)
    _expect_same_items("cart", cart.open(), expected_names)
    cart.checkout()

    checkout = CheckoutPage(page)
    checkout.fill_customer(order.customer)
    _expect_same_items("checkout overview", checkout.overview_items(), expected_names)

    totals = checkout.read_totals()
    result.totals = totals
    check_totals(found, totals)
    log.info("Totals verified: %s", totals)

    result.confirmation_message = checkout.finish()
    page.screenshot(path=str(out_dir / "confirmation.png"), full_page=True)
    result.ordered_items = expected_names
    result.status = "success"
    log.info("Order placed: %s", result.confirmation_message)


def _expect_same_items(where: str, actual: list, expected: list) -> None:
    if sorted(actual) != sorted(expected):
        raise BotError(f"Unexpected items in {where}: expected {sorted(expected)}, got {sorted(actual)}")


def _write_products(catalog, out_dir: Path) -> None:
    data = [{"name": p.name, "description": p.description, "price": float(p.price)} for p in catalog]
    (out_dir / "products.json").write_text(json.dumps(data, indent=2) + "\n")


def _save_failure_screenshot(page, out_dir: Path) -> None:
    try:
        page.screenshot(path=str(out_dir / "failure.png"), full_page=True)
    except Exception:  # best effort only
        pass
