"""
Seed a shop with default Papers, FinishingRates, and Products.
Papers are shop resources — not created per machine.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from printy_api.shops.models import (
    FinishingRate,
    Paper,
    Product,
    SheetSize,
    Shop,
)


# Common paper specs: (name, gsm, price_per_sheet)
PAPER_SPECS = [
    # Uncoated
    ("Uncoated", 80, "0.08"),
    ("Uncoated", 100, "0.10"),
    ("Uncoated", 115, "0.12"),
    # Silk
    ("Silk", 115, "0.14"),
    ("Silk", 150, "0.18"),
    ("Silk", 170, "0.22"),
    ("Silk", 250, "0.30"),
    ("Silk", 300, "0.38"),
    # Matt
    ("Matt", 115, "0.15"),
    ("Matt", 150, "0.20"),
    ("Matt", 170, "0.24"),
    ("Matt", 250, "0.32"),
    ("Matt", 350, "0.42"),
    # Gloss
    ("Gloss", 115, "0.14"),
    ("Gloss", 150, "0.19"),
    ("Gloss", 170, "0.23"),
    ("Gloss", 250, "0.31"),
    ("Gloss", 300, "0.40"),
]

# Finishing rates: (name, rate_per_unit, unit_label)
FINISHING_SPECS = [
    ("Lamination Matte (per side)", "0.05", "side"),
    ("Lamination Gloss (per side)", "0.05", "side"),
    ("Cutting (flat)", "0.01", "cut"),
    ("Cutting (guillotine)", "0.02", "cut"),
    ("Folding", "0.015", "fold"),
    ("Saddle stitch binding", "0.08", "book"),
    ("Perfect bind", "0.15", "book"),
    ("Wire-O binding", "0.12", "book"),
]

# Products: (name, slug, description)
PRODUCT_SPECS = [
    (
        "Business Cards",
        "business-cards",
        "Standard business cards, 85x55mm. Sheet-fed.",
    ),
    (
        "Flyers",
        "flyers",
        "Marketing flyers. Sheet-fed.",
    ),
    (
        "Roll-up Banner",
        "roll-up-banner",
        "Large format roll-up / pull-up banner.",
    ),
]


def get_or_create_sheet_sizes():
    """Ensure A4, A3, SRA3 exist (global)."""
    sizes = [
        ("A4", 210, 297),
        ("A3", 297, 420),
        ("SRA3", 320, 450),
    ]
    result = {}
    for name, w, h in sizes:
        obj, _ = SheetSize.objects.get_or_create(
            name=name,
            defaults={"width_mm": w, "height_mm": h},
        )
        result[name] = obj
    return result


def seed_papers(shop: Shop, sizes: dict) -> dict:
    """Create common Papers for A4, A3, SRA3. Returns {size_name: first_paper} for defaults."""
    first_by_size = {}
    for size_name, sheet_size in sizes.items():
        for name, gsm, price in PAPER_SPECS:
            full_name = f"{name} {gsm}gsm"
            paper, created = Paper.objects.get_or_create(
                shop=shop,
                name=full_name,
                sheet_size=sheet_size,
                gsm=gsm,
                defaults={
                    "price_per_sheet": Decimal(price),
                    "is_active": True,
                },
            )
            if size_name not in first_by_size:
                first_by_size[size_name] = paper
    return first_by_size


def seed_finishing_rates(shop: Shop) -> None:
    """Create common FinishingRate rows."""
    for name, rate, unit in FINISHING_SPECS:
        FinishingRate.objects.get_or_create(
            shop=shop,
            name=name,
            defaults={
                "rate_per_unit": Decimal(rate),
                "unit_label": unit,
                "is_active": True,
            },
        )


def seed_products(shop: Shop, first_by_size: dict) -> None:
    """Create Business Cards, Flyers, Roll-up products."""
    a4_paper = first_by_size.get("A4")
    sra3_paper = first_by_size.get("SRA3")

    for name, slug, description in PRODUCT_SPECS:
        if "Roll-up" in name or "roll-up" in slug:
            default_paper = sra3_paper
        else:
            default_paper = a4_paper

        Product.objects.get_or_create(
            shop=shop,
            slug=slug,
            defaults={
                "name": name,
                "description": description,
                "default_paper": default_paper,
                "default_machine": None,
                "is_active": True,
            },
        )


class Command(BaseCommand):
    help = "Seed a shop with default Papers, FinishingRates, and Products"

    def add_arguments(self, parser):
        parser.add_argument(
            "--shop",
            type=str,
            required=True,
            help="Shop ID or slug",
        )

    def handle(self, *args, **options):
        shop_ref = options["shop"]

        # Resolve shop by id or slug
        if shop_ref.isdigit():
            shop = Shop.objects.filter(pk=int(shop_ref)).first()
        else:
            shop = Shop.objects.filter(slug=shop_ref).first()

        if not shop:
            self.stderr.write(
                self.style.ERROR(f"Shop not found: {shop_ref}")
            )
            return

        self.stdout.write(f"Seeding shop: {shop.name} (id={shop.pk})")

        sizes = get_or_create_sheet_sizes()
        first_by_size = seed_papers(shop, sizes)
        seed_finishing_rates(shop)
        seed_products(shop, first_by_size)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded: {Paper.objects.filter(shop=shop).count()} papers, "
                f"{FinishingRate.objects.filter(shop=shop).count()} finishing rates, "
                f"{Product.objects.filter(shop=shop).count()} products."
            )
        )
