"""
Pricing models: PrintingRate, FinishingRate, Material.
"""
from decimal import Decimal
from django.db import models

from common.models import TimeStampedModel


class PrintingRate(TimeStampedModel):
    """Machine-scoped printing rate. No shop FK (machine has shop)."""

    COLOR_MODE_CHOICES = [
        ("BW", "Black & White"),
        ("COLOR", "Color"),
    ]
    SIDES_CHOICES = [
        ("SIMPLEX", "Simplex (1 side)"),
        ("DUPLEX", "Duplex (2 sides)"),
    ]

    machine = models.ForeignKey(
        "inventory.Machine", on_delete=models.CASCADE, related_name="printing_rates"
    )
    sheet_size = models.CharField(max_length=20)
    color_mode = models.CharField(max_length=10, choices=COLOR_MODE_CHOICES)
    sides = models.CharField(max_length=10, choices=SIDES_CHOICES)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Printing Rate"
        verbose_name_plural = "Printing Rates"
        constraints = [
            models.UniqueConstraint(
                fields=["machine", "sheet_size", "color_mode", "sides"],
                name="unique_machine_printing_rate",
            )
        ]

    def __str__(self):
        return f"{self.machine.name} {self.sheet_size} {self.color_mode} {self.sides}"


class FinishingRate(TimeStampedModel):
    """Shop-scoped finishing rate."""

    CHARGE_UNIT_CHOICES = [
        ("PER_PIECE", "Per Piece"),
        ("PER_SIDE", "Per Side"),
        ("PER_SQM", "Per Square Meter"),
        ("FLAT", "Flat"),
    ]

    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE, related_name="finishing_rates"
    )
    name = models.CharField(max_length=255)
    charge_unit = models.CharField(max_length=20, choices=CHARGE_UNIT_CHOICES)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    setup_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    min_qty = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Finishing Rate"
        verbose_name_plural = "Finishing Rates"

    def __str__(self):
        return f"{self.name} ({self.shop.name})"


class Material(TimeStampedModel):
    """Shop-scoped material (e.g. vinyl for large format)."""

    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE, related_name="materials"
    )
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=20, default="SQM")
    buying_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materials"

    def __str__(self):
        return f"{self.name} ({self.shop.name})"
