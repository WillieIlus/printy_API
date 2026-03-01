"""
Catalog models: Product and ProductFinishingOption.
Single product/template system.
"""
from decimal import Decimal
from django.db import models

from common.models import TimeStampedModel


class Product(TimeStampedModel):
    """Product template, shop-scoped."""

    PRICING_MODE_CHOICES = [
        ("SHEET", "Sheet"),
        ("LARGE_FORMAT", "Large Format"),
    ]
    SIDES_CHOICES = [
        ("SIMPLEX", "Simplex"),
        ("DUPLEX", "Duplex"),
    ]

    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    pricing_mode = models.CharField(max_length=20, choices=PRICING_MODE_CHOICES)
    default_finished_width_mm = models.IntegerField(null=True, blank=True)
    default_finished_height_mm = models.IntegerField(null=True, blank=True)
    default_bleed_mm = models.IntegerField(default=3)
    default_sides = models.CharField(max_length=10, choices=SIDES_CHOICES, default="SIMPLEX")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} ({self.shop.name})"


class ProductFinishingOption(TimeStampedModel):
    """Finishing option available for a product."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="finishing_options"
    )
    finishing_rate = models.ForeignKey(
        "pricing.FinishingRate", on_delete=models.CASCADE, related_name="product_options"
    )
    is_default = models.BooleanField(default=False)
    price_adjustment = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = "Product Finishing Option"
        verbose_name_plural = "Product Finishing Options"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "finishing_rate"],
                name="unique_product_finishing",
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.finishing_rate.name}"
