"""
Seed Printy API with sample data.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from printy_api.shops.models import (
    SheetSize,
    Shop,
    Paper,
    Machine,
    FinishingRate,
    Material,
    Product,
    ProductOption,
    QuoteRequest,
    QuoteItem,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed Printy API with sample shop, products, and quote"

    def handle(self, *args, **options):
        self.stdout.write("Seeding...")

        # Sheet sizes
        a4, _ = SheetSize.objects.get_or_create(
            name="A4",
            defaults={"width_mm": 210, "height_mm": 297},
        )
        sra3, _ = SheetSize.objects.get_or_create(
            name="SRA3",
            defaults={"width_mm": 320, "height_mm": 450},
        )

        # Users
        seller, _ = User.objects.get_or_create(
            username="seller",
            defaults={"email": "seller@printy.test", "is_staff": True},
        )
        if _:
            seller.set_password("seller123")
            seller.save()
        buyer, _ = User.objects.get_or_create(
            username="buyer",
            defaults={"email": "buyer@printy.test"},
        )
        if _:
            buyer.set_password("buyer123")
            buyer.save()

        # Shop
        shop, _ = Shop.objects.get_or_create(
            slug="acme-print",
            defaults={
                "name": "Acme Print Shop",
                "owner": seller,
            },
        )

        # Paper
        paper1, _ = Paper.objects.get_or_create(
            shop=shop,
            name="Silk 300gsm",
            sheet_size=a4,
            gsm=300,
            defaults={"price_per_sheet": Decimal("0.15"), "is_active": True},
        )
        paper2, _ = Paper.objects.get_or_create(
            shop=shop,
            name="Matt 350gsm",
            sheet_size=a4,
            gsm=350,
            defaults={"price_per_sheet": Decimal("0.22"), "is_active": True},
        )

        # Machine
        machine, _ = Machine.objects.get_or_create(
            shop=shop,
            name="HP Indigo A4",
            sheet_size=a4,
            defaults={
                "gsm_min": 80,
                "gsm_max": 400,
                "cost_per_impression": Decimal("0.02"),
                "is_active": True,
            },
        )

        # Finishing
        cutting, _ = FinishingRate.objects.get_or_create(
            shop=shop,
            name="Cutting",
            defaults={"rate_per_unit": Decimal("0.01"), "unit_label": "cut", "is_active": True},
        )

        # Material (optional)
        laminate, _ = Material.objects.get_or_create(
            shop=shop,
            name="Matt Laminate",
            defaults={"price_per_unit": Decimal("0.05"), "unit_label": "sheet", "is_active": True},
        )

        # Product
        product, _ = Product.objects.get_or_create(
            shop=shop,
            slug="business-cards",
            defaults={
                "name": "Business Cards",
                "description": "Standard business cards, 85x55mm",
                "default_paper": paper1,
                "default_machine": machine,
                "is_active": True,
            },
        )
        ProductOption.objects.get_or_create(
            product=product,
            paper=paper1,
            machine=machine,
            defaults={},
        )
        ProductOption.objects.get_or_create(
            product=product,
            paper=paper2,
            machine=machine,
            defaults={},
        )

        # Quote request (one sample draft per buyer/shop)
        quote = QuoteRequest.objects.filter(
            shop=shop, buyer=buyer, status=QuoteRequest.Status.DRAFT
        ).first()
        if not quote:
            quote = QuoteRequest.objects.create(
                shop=shop, buyer=buyer, status=QuoteRequest.Status.DRAFT
            )
        if not quote.items.exists():
            QuoteItem.objects.create(
                quote_request=quote,
                product=product,
                quantity=500,
                paper=paper1,
                machine=machine,
                finishing_rate=cutting,
                finishing_quantity=4,
            )

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
        self.stdout.write("  Seller: seller / seller123")
        self.stdout.write("  Buyer: buyer / buyer123")
        self.stdout.write("  Shop: acme-print")
