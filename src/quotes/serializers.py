"""
Quote serializers.
"""
from rest_framework import serializers

from .models import QuoteRequest, QuoteItem, QuoteItemFinishing


class QuoteItemFinishingSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteItemFinishing
        fields = ("id", "finishing_rate", "coverage_qty", "price_override")

    def validate_finishing_rate(self, value):
        quote = self.context.get("quote_request")
        if quote and value.shop_id != quote.shop_id:
            raise serializers.ValidationError("Finishing rate must belong to the quote's shop.")
        return value


class QuoteItemSerializer(serializers.ModelSerializer):
    finishings = QuoteItemFinishingSerializer(many=True, required=False)

    class Meta:
        model = QuoteItem
        fields = (
            "id", "product", "quantity", "pricing_mode",
            "paper", "material", "chosen_width_mm", "chosen_height_mm",
            "sides", "color_mode", "machine",
            "special_instructions",
            "unit_price", "line_total", "finishings",
        )
        read_only_fields = ("unit_price", "line_total")

    def validate(self, data):
        quote = self.context.get("quote_request") or (self.instance.quote_request if self.instance else None)
        if not quote:
            return data

        if quote.status != "DRAFT":
            raise serializers.ValidationError("Cannot modify items when quote is not in DRAFT status.")

        pricing_mode = data.get("pricing_mode", getattr(self.instance, "pricing_mode", None))
        if pricing_mode == "SHEET":
            if not data.get("paper"):
                raise serializers.ValidationError({"paper": "Paper is required for SHEET pricing mode."})
            paper = data.get("paper")
            if paper and paper.shop_id != quote.shop_id:
                raise serializers.ValidationError({"paper": "Paper must belong to the quote's shop."})
        elif pricing_mode == "LARGE_FORMAT":
            if not data.get("material"):
                raise serializers.ValidationError({"material": "Material is required for LARGE_FORMAT."})
            if not data.get("chosen_width_mm") or not data.get("chosen_height_mm"):
                raise serializers.ValidationError(
                    "chosen_width_mm and chosen_height_mm are required for LARGE_FORMAT."
                )
            material = data.get("material")
            if material and material.shop_id != quote.shop_id:
                raise serializers.ValidationError({"material": "Material must belong to the quote's shop."})

        machine = data.get("machine")
        if machine and machine.shop_id != quote.shop_id:
            raise serializers.ValidationError({"machine": "Machine must belong to the quote's shop."})

        return data

    def create(self, validated_data):
        finishings_data = validated_data.pop("finishings", [])
        item = QuoteItem.objects.create(**validated_data)
        for f in finishings_data:
            QuoteItemFinishing.objects.create(quote_item=item, **f)
        return item

    def update(self, instance, validated_data):
        finishings_data = validated_data.pop("finishings", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if finishings_data is not None:
            for f in finishings_data:
                QuoteItemFinishing.objects.update_or_create(
                    quote_item=instance,
                    finishing_rate=f["finishing_rate"],
                    defaults={
                        "coverage_qty": f.get("coverage_qty"),
                        "price_override": f.get("price_override"),
                    },
                )
        return instance


class QuoteRequestSerializer(serializers.ModelSerializer):
    items = QuoteItemSerializer(many=True, read_only=True)

    class Meta:
        model = QuoteRequest
        fields = (
            "id", "shop", "created_by", "customer_name", "customer_email", "customer_phone",
            "status", "notes", "total", "pricing_locked_at",
            "items", "created_at", "updated_at",
        )
        read_only_fields = ("total", "pricing_locked_at", "created_by", "status")

class QuoteRequestCreateSerializer(serializers.ModelSerializer):
    """For create - buyer can create for any active shop (browse catalog first)."""
    class Meta:
        model = QuoteRequest
        fields = ("shop", "customer_name", "customer_email", "customer_phone", "notes")

    def validate_shop(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Shop is not active.")
        return value
