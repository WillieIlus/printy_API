"""
Shop model - core tenant for print shop SaaS.
"""
from django.db import models

from accounts.models import User
from common.models import TimeStampedModel


class Shop(TimeStampedModel):
    """Shop owned by a seller. All resources are shop-scoped."""

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shops")
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=100)
    currency = models.CharField(max_length=3, default="KES")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Shop"
        verbose_name_plural = "Shops"

    def __str__(self):
        return self.name
