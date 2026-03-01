"""
Shop serializers.
"""
from rest_framework import serializers

from .models import Shop
from inventory.models import Machine, Paper
from inventory.serializers import MachineSerializer, PaperSerializer
from pricing.models import FinishingRate, Material
from catalog.models import Product, ProductFinishingOption


class ShopListSerializer(serializers.ModelSerializer):
    """Minimal for public listing."""

    class Meta:
        model = Shop
        fields = ("id", "name", "slug")


class ShopDetailSerializer(serializers.ModelSerializer):
    """Full shop for seller management."""

    class Meta:
        model = Shop
        fields = ("id", "name", "slug", "currency", "is_active", "created_at")


class FinishingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinishingRate
        fields = ("id", "name", "charge_unit", "price", "setup_fee", "min_qty", "is_active")


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ("id", "name", "unit", "buying_price", "selling_price", "is_active")


class ProductFinishingOptionSerializer(serializers.ModelSerializer):
    finishing_rate_name = serializers.CharField(source="finishing_rate.name", read_only=True)

    class Meta:
        model = ProductFinishingOption
        fields = ("id", "finishing_rate", "finishing_rate_name", "is_default", "price_adjustment")


class ProductCatalogSerializer(serializers.ModelSerializer):
    """Product with finishing options for public catalog."""
    finishing_options = ProductFinishingOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "description", "category", "pricing_mode",
            "default_finished_width_mm", "default_finished_height_mm",
            "default_bleed_mm", "default_sides", "finishing_options"
        )


class ShopCatalogSerializer(serializers.ModelSerializer):
    """Shop with products for public catalog view."""
    products = ProductCatalogSerializer(many=True, read_only=True)

    class Meta:
        model = Shop
        fields = ("id", "name", "slug", "products")
