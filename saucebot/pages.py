"""Thin page objects. Every step waits on page state (selectors/URLs), never on time."""
import re
from playwright.sync_api import Page, expect, TimeoutError as PWTimeout

from .models import BotError, Product, Totals, parse_price


class LoginPage:
    def __init__(self, page: Page, base_url: str):
        self.page, self.base_url = page, base_url

    def login(self, username: str, password: str) -> None:
        self.page.goto(self.base_url)
        self.page.fill("[data-test=username]", username)
        self.page.fill("[data-test=password]", password)
        self.page.click("[data-test=login-button]")
        # Succeeds on whichever comes first: the inventory list or an error banner.
        # This is what absorbs the slow login of performance_glitch_user.
        self.page.locator(".inventory_item, [data-test=error]").first.wait_for()
        if self.page.locator("[data-test=error]").count():
            raise BotError("Login failed: " + self.page.locator("[data-test=error]").inner_text())


class InventoryPage:
    def __init__(self, page: Page):
        self.page = page

    def collect_products(self) -> list:
        cards = self.page.locator("[data-test=inventory-item]")
        expect(cards.first).to_be_visible()
        products = []
        for i in range(cards.count()):
            card = cards.nth(i)
            products.append(
                Product(
                    name=card.locator("[data-test=inventory-item-name]").inner_text().strip(),
                    description=card.locator("[data-test=inventory-item-desc]").inner_text().strip(),
                    price=parse_price(card.locator("[data-test=inventory-item-price]").inner_text()),
                )
            )
        return products

    def add_to_cart(self, name: str) -> None:
        cards = self.page.locator("[data-test=inventory-item]")
        for i in range(cards.count()):
            card = cards.nth(i)
            if card.locator("[data-test=inventory-item-name]").inner_text().strip() == name:
                card.get_by_role("button", name="Add to cart").click()
                expect(card.get_by_role("button", name="Remove")).to_be_visible()
                return
        raise BotError(f"Item disappeared from the inventory page: {name}")


class CartPage:
    def __init__(self, page: Page, base_url: str):
        self.page, self.base_url = page, base_url

    def open(self) -> list:
        self.page.click("[data-test=shopping-cart-link]")
        self.page.wait_for_url(re.compile(r"/cart\.html"))
        # The URL changes before the new view renders, so also wait for the cart
        # itself. Reading names too early would return the inventory page's items.
        expect(self.page.locator("[data-test=cart-list]")).to_be_visible()
        return self.item_names()

    def item_names(self) -> list:
        names = self.page.locator("[data-test=cart-list] [data-test=inventory-item-name]")
        return [n.strip() for n in names.all_inner_texts()]

    def checkout(self) -> None:
        self.page.click("[data-test=checkout]")
        self.page.wait_for_url(re.compile(r"/checkout-step-one\.html"))


class CheckoutPage:
    def __init__(self, page: Page):
        self.page = page

    def fill_customer(self, customer) -> None:
        self.page.fill("[data-test=firstName]", customer.first_name)
        self.page.fill("[data-test=lastName]", customer.last_name)
        self.page.fill("[data-test=postalCode]", customer.zip)
        self.page.click("[data-test=continue]")
        self.page.locator("[data-test=checkout-summary-container], [data-test=error]").first.wait_for()
        if self.page.locator("[data-test=error]").count():
            raise BotError("Checkout form rejected: " + self.page.locator("[data-test=error]").inner_text())

    def overview_items(self) -> list:
        names = self.page.locator("[data-test=checkout-summary-container] [data-test=inventory-item-name]")
        return [n.strip() for n in names.all_inner_texts()]

    def read_totals(self) -> Totals:
        return Totals(
            item_total=parse_price(self.page.locator("[data-test=subtotal-label]").inner_text()),
            tax=parse_price(self.page.locator("[data-test=tax-label]").inner_text()),
            total=parse_price(self.page.locator("[data-test=total-label]").inner_text()),
        )

    def finish(self) -> str:
        self.page.click("[data-test=finish]")
        self.page.wait_for_url(re.compile(r"/checkout-complete\.html"))
        header = self.page.locator("[data-test=complete-header]")
        expect(header).to_be_visible()
        return header.inner_text().strip()
