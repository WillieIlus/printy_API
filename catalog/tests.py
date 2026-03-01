"""Tests for catalog app."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.choices import PricingMode
from catalog.models import Product
from catalog.services import compute_product_price_range_est
from inventory.choices import MachineType, PaperType, SheetSize
from inventory.models import Machine, Paper
from pricing.choices import ColorMode, Sides
from pricing.models import PrintingRate
from shops.models import Shop

User = get_user_model()


class ProductPriceRangeEstTests(TestCase):
    """Tests for compute_product_price_range_est."""

    def setUp(self):
        self.user = User.objects.create_user(email="s@test.com", password="pass")
        self.shop = Shop.objects.create(
            owner=self.user, name="Test Shop", slug="test-shop", is_active=True
        )
        self.product = Product.objects.create(
            shop=self.shop,
            name="Flyer",
            pricing_mode=PricingMode.SHEET,
            default_finished_width_mm=210,
            default_finished_height_mm=297,
            default_sides=Sides.SIMPLEX,
            min_quantity=1,
        )
        self.machine = Machine.objects.create(
            shop=self.shop,
            name="Digital Press",
            machine_type=MachineType.DIGITAL,
            max_width_mm=450,
            max_height_mm=320,
        )

    def test_multiple_papers_lowest_uses_cheapest_highest_uses_most_expensive(self):
        """When multiple papers exist, lowest uses cheapest total, highest uses most expensive."""
        Paper.objects.create(
            shop=self.shop,
            sheet_size=SheetSize.SRA3,
            gsm=130,
            paper_type=PaperType.GLOSS,
            buying_price=Decimal("5"),
            selling_price=Decimal("15"),
            width_mm=320,
            height_mm=450,
        )
        Paper.objects.create(
            shop=self.shop,
            sheet_size=SheetSize.SRA3,
            gsm=300,
            paper_type=PaperType.MATTE,
            buying_price=Decimal("20"),
            selling_price=Decimal("45"),
            width_mm=320,
            height_mm=450,
        )
        PrintingRate.objects.create(
            machine=self.machine,
            sheet_size=SheetSize.SRA3,
            color_mode=ColorMode.COLOR,
            single_price=Decimal("12"),
            double_price=Decimal("20"),
        )
        result = compute_product_price_range_est(self.product)
        self.assertTrue(result["can_calculate"])
        self.assertEqual(result["lowest"]["unit_price"], 27.0)  # 15 + 12
        self.assertEqual(result["highest"]["unit_price"], 57.0)  # 45 + 12
        self.assertIn("130gsm", result["lowest"]["paper_label"])
        self.assertIn("300gsm", result["highest"]["paper_label"])
        self.assertEqual(result["lowest"]["total"], 27.0)
        self.assertEqual(result["highest"]["total"], 57.0)

    def test_missing_printing_rate_includes_add_printing_rate_suggestion(self):
        """When missing printing rate, missing_fields includes printing_rate and suggestions include ADD_PRINTING_RATE."""
        Paper.objects.create(
            shop=self.shop,
            sheet_size=SheetSize.SRA3,
            gsm=130,
            paper_type=PaperType.GLOSS,
            buying_price=Decimal("5"),
            selling_price=Decimal("15"),
            width_mm=320,
            height_mm=450,
        )
        # No PrintingRate for SRA3
        result = compute_product_price_range_est(self.product)
        self.assertFalse(result["can_calculate"])
        self.assertIn("printing_rate", result["missing_fields"])
        codes = [s["code"] for s in result["suggestions"]]
        self.assertIn("ADD_PRINTING_RATE", codes)
        self.assertIsNone(result["lowest"]["total"])
        self.assertIsNone(result["highest"]["total"])
