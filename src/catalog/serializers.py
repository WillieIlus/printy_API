"""
Catalog serializers.
"""
from rest_framework import serializers

from .models import Product, ProductFinishingOption


class ProductFinishingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFinishingOption
        fields = ("id", "finishing_rate", "is_default", "price_adjustment")


class ProductSerializer(serializers.ModelSerializer):
    finishing_options = ProductFinishingOptionSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = (
            "id", "name", "description", "category", "pricing_mode",
            "default_finished_width_mm", "default_finished_height_mm",
            "default_bleed_mm", "default_sides", "is_active", "finishing_options"
        )

    def create(self, validated_data):
        finishing_data = validated_data.pop("finishing_options", [])
        product = Product.objects.create(**validated_data)
        for opt in finishing_data:
            fr = opt["finishing_rate"]
            if fr.shop_id != product.shop_id:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"finishing_options": "Finishing rate must belong to the product's shop."})
            ProductFinishingOption.objects.create(product=product, **opt)
        return product

    def update(self, instance, validated_data):
        finishing_data = validated_data.pop("finishing_options", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if finishing_data is not None:
            instance.finishing_options.exclude(
                finishing_rate__in=[o["finishing_rate"] for o in finishing_data]
            ).delete()
            for opt in finishing_data:
                ProductFinishingOption.objects.update_or_create(
                    product=instance,
                    finishing_rate=opt["finishing_rate"],
                    defaults={
                        "is_default": opt.get("is_default", False),
                        "price_adjustment": opt.get("price_adjustment"),
                    },
                )
        return instance
