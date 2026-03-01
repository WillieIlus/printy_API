"""Choice enums for catalog app."""

from django.db import models


class PricingMode(models.TextChoices):
    SHEET = "SHEET", "Sheet"
    LARGE_FORMAT = "LARGE_FORMAT", "Large Format"
