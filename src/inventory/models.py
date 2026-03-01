"""
Inventory models: Machine and Paper.
Paper is shop-scoped, NOT linked to Machine via FK/M2M.
Compatibility validated by sheet_size and optional gsm range.
"""
from decimal import Decimal
from django.db import models

from common.models import TimeStampedModel


SHEET_SIZE_CHOICES = [
    ("A4", "A4"),
    ("A3", "A3"),
    ("SRA3", "SRA3"),
    ("A2", "A2"),
    ("B2", "B2"),
    ("Custom", "Custom"),
]

# Standard dimensions in mm (width, height)
SHEET_DIMENSIONS = {
    "A4": (210, 297),
    "A3": (297, 420),
    "SRA3": (320, 450),
    "A2": (420, 594),
    "B2": (500, 707),
}


class Machine(TimeStampedModel):
    """Printing machine, shop-scoped."""

    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE, related_name="machines"
    )
    name = models.CharField(max_length=255)
    machine_type = models.CharField(max_length=100)
    max_width_mm = models.IntegerField()
    max_height_mm = models.IntegerField()
    min_gsm = models.IntegerField(null=True, blank=True)
    max_gsm = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Machine"
        verbose_name_plural = "Machines"

    def __str__(self):
        return f"{self.name} ({self.shop.name})"


class Paper(TimeStampedModel):
    """Paper stock, shop-scoped. No FK to Machine."""

    PAPER_TYPE_CHOICES = [
        ("GLOSS", "Gloss"),
        ("MATTE", "Matte"),
        ("OFFSET", "Offset"),
        ("NEWSPRINT", "Newsprint"),
        ("CARD", "Card"),
    ]

    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE, related_name="papers"
    )
    sheet_size = models.CharField(max_length=20, choices=SHEET_SIZE_CHOICES)
    gsm = models.IntegerField()
    paper_type = models.CharField(max_length=20, choices=PAPER_TYPE_CHOICES)
    width_mm = models.IntegerField(null=True, blank=True)
    height_mm = models.IntegerField(null=True, blank=True)
    buying_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_in_stock = models.IntegerField(null=True, blank=True)
    reorder_level = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Paper"
        verbose_name_plural = "Papers"
        constraints = [
            models.UniqueConstraint(
                fields=["shop", "sheet_size", "gsm", "paper_type"],
                name="unique_shop_paper",
            )
        ]

    def save(self, *args, **kwargs):
        if self.sheet_size != "Custom" and self.sheet_size in SHEET_DIMENSIONS:
            w, h = SHEET_DIMENSIONS[self.sheet_size]
            if not self.width_mm:
                self.width_mm = w
            if not self.height_mm:
                self.height_mm = h
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sheet_size} {self.gsm}gsm {self.get_paper_type_display()}"
