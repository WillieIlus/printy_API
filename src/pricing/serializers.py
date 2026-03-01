"""
Pricing serializers.
"""
from rest_framework import serializers

from .models import PrintingRate, FinishingRate, Material


class PrintingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintingRate
        fields = ("id", "sheet_size", "color_mode", "sides", "price", "is_active")


class FinishingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinishingRate
        fields = ("id", "name", "charge_unit", "price", "setup_fee", "min_qty", "is_active")


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ("id", "name", "unit", "buying_price", "selling_price", "is_active")
