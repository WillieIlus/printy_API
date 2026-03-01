"""API endpoint tests."""
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from catalog.choices import PricingMode
from catalog.models import Product
from pricing.choices import Sides
from shops.models import Shop


class PublicShopsAPITestCase(TestCase):
    """Test public shop and catalog endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="s@t.com", password="pass")
        self.shop = Shop.objects.create(
            owner=self.user, name="Test Shop", slug="test-shop", is_active=True
        )
        Product.objects.create(
            shop=self.shop,
            name="Business Card",
            pricing_mode=PricingMode.SHEET,
            default_finished_width_mm=90,
            default_finished_height_mm=55,
            default_bleed_mm=3,
            default_sides=Sides.SIMPLEX,
            is_active=True,
        )

    def test_list_public_shops(self):
        response = self.client.get("/api/public/shops/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data.get("results", data)  # Paginated or raw list
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["slug"], "test-shop")

    def test_catalog_by_slug(self):
        response = self.client.get("/api/public/shops/test-shop/catalog/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Business Card")


class QuoteRequestAPITestCase(TestCase):
    """Test quote request buyer flow."""

    def setUp(self):
        self.client = APIClient()
        self.buyer = User.objects.create_user(email="b@t.com", password="pass")
        self.seller = User.objects.create_user(email="s@t.com", password="pass")
        self.shop = Shop.objects.create(
            owner=self.seller, name="Test Shop", slug="test-shop", is_active=True
        )
        self.product = Product.objects.create(
            shop=self.shop,
            name="Business Card",
            pricing_mode=PricingMode.SHEET,
            default_finished_width_mm=90,
            default_finished_height_mm=55,
            default_bleed_mm=3,
            default_sides=Sides.SIMPLEX,
            is_active=True,
        )

    def test_buyer_creates_and_submits_quote(self):
        self.client.force_authenticate(user=self.buyer)
        # Create
        r = self.client.post(
            "/api/quote-requests/",
            {"shop": self.shop.id, "customer_name": "Buyer", "customer_email": "b@t.com"},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        qr_id = r.json()["id"]
        # Add item
        r2 = self.client.post(
            f"/api/quote-requests/{qr_id}/items/",
            {"product": self.product.id, "quantity": 100, "pricing_mode": PricingMode.SHEET},
            format="json",
        )
        self.assertEqual(r2.status_code, 201)
        # Submit
        r3 = self.client.post(f"/api/quote-requests/{qr_id}/submit/")
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["status"], "SUBMITTED")
