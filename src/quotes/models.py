"""
Quote models: QuoteRequest, QuoteItem, QuoteItemFinishing.
Direct FK references to avoid attribute-based lookups (no MultipleObjectsReturned).
"""
from decimal import Decimal
from django.db import models

from common.models import TimeStampedModel


class QuoteRequest(TimeStampedModel):
    """Quote request - buyer creates, seller prices."""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("PRICED", "Priced"),
        ("SENT", "Sent"),
        ("ACCEPTED", "Accepted"),
        ("REJECTED", "Rejected"),
    ]

    shop = models.ForeignKey(
        "shops.Shop", on_delete=models.CASCADE, related_name="quote_requests"
    )
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="quote_requests"
    )
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    notes = models.TextField(blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pricing_locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Quote Request"
        verbose_name_plural = "Quote Requests"

    def __str__(self):
        return f"Quote #{self.id} - {self.customer_name} ({self.status})"


class QuoteItem(TimeStampedModel):
    """Single item in a quote. Stores direct FK refs to chosen resources."""

    PRICING_MODE_CHOICES = [
        ("SHEET", "Sheet"),
        ("LARGE_FORMAT", "Large Format"),
    ]
    SIDES_CHOICES = [
        ("SIMPLEX", "Simplex"),
        ("DUPLEX", "Duplex"),
    ]
    COLOR_MODE_CHOICES = [
        ("BW", "Black & White"),
        ("COLOR", "Color"),
    ]

    quote_request = models.ForeignKey(
        QuoteRequest, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="quote_items"
    )
    quantity = models.IntegerField()
    pricing_mode = models.CharField(max_length=20, choices=PRICING_MODE_CHOICES)

    # SHEET: paper required
    paper = models.ForeignKey(
        "inventory.Paper", on_delete=models.SET_NULL, null=True, blank=True, related_name="quote_items"
    )
    # LARGE_FORMAT: material + dims required
    material = models.ForeignKey(
        "pricing.Material", on_delete=models.SET_NULL, null=True, blank=True, related_name="quote_items"
    )
    chosen_width_mm = models.IntegerField(null=True, blank=True)
    chosen_height_mm = models.IntegerField(null=True, blank=True)

    sides = models.CharField(max_length=10, choices=SIDES_CHOICES, blank=True)
    color_mode = models.CharField(max_length=10, choices=COLOR_MODE_CHOICES, blank=True)
    machine = models.ForeignKey(
        "inventory.Machine", on_delete=models.SET_NULL, null=True, blank=True, related_name="quote_items"
    )

    special_instructions = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pricing_locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Quote Item"
        verbose_name_plural = "Quote Items"

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.pricing_mode == "SHEET" and not self.paper:
            raise ValidationError({"paper": "Paper is required for SHEET pricing mode."})
        if self.pricing_mode == "LARGE_FORMAT":
            if not self.material:
                raise ValidationError({"material": "Material is required for LARGE_FORMAT."})
            if not self.chosen_width_mm or not self.chosen_height_mm:
                raise ValidationError(
                    {"chosen_width_mm": "Dimensions required for LARGE_FORMAT."}
                )
        if self.paper and self.quote_request_id and self.paper.shop_id != self.quote_request.shop_id:
            raise ValidationError({"paper": "Paper must belong to the quote's shop."})
        if self.material and self.quote_request_id and self.material.shop_id != self.quote_request.shop_id:
            raise ValidationError({"material": "Material must belong to the quote's shop."})
        if self.machine and self.quote_request_id and self.machine.shop_id != self.quote_request.shop_id:
            raise ValidationError({"machine": "Machine must belong to the quote's shop."})


class QuoteItemFinishing(TimeStampedModel):
    """Finishing applied to a quote item."""

    quote_item = models.ForeignKey(
        QuoteItem, on_delete=models.CASCADE, related_name="finishings"
    )
    finishing_rate = models.ForeignKey(
        "pricing.FinishingRate", on_delete=models.CASCADE, related_name="quote_item_finishings"
    )
    coverage_qty = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    price_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Quote Item Finishing"
        verbose_name_plural = "Quote Item Finishings"
        constraints = [
            models.UniqueConstraint(
                fields=["quote_item", "finishing_rate"],
                name="unique_quote_item_finishing",
            )
        ]

    def __str__(self):
        return f"{self.quote_item} - {self.finishing_rate.name}"
