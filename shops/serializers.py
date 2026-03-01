"""Serializers for shop models."""
from rest_framework import serializers

from .models import (
    Shop, Machine, Paper, PrintingRate, FinishingRate, Material,
    Product, ProductFinishingOption,
)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'owner', 'created_at', 'updated_at']
        read_only_fields = ['owner', 'created_at', 'updated_at']


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ['id', 'shop', 'name', 'created_at']


class PaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paper
        fields = ['id', 'shop', 'name', 'created_at']


class PrintingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintingRate
        fields = ['id', 'shop', 'name', 'rate', 'created_at']


class FinishingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinishingRate
        fields = ['id', 'shop', 'name', 'rate', 'created_at']


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'shop', 'name', 'unit_price', 'created_at']


class ProductFinishingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFinishingOption
        fields = ['id', 'product', 'name', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    finishing_options = ProductFinishingOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'shop', 'name', 'description', 'finishing_options', 'created_at', 'updated_at']
