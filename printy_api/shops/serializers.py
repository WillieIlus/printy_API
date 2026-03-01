"""
DRF serializers for Printy API.
"""
from decimal import Decimal
from rest_framework import serializers
from .models import (
    User,
    Shop,
    SheetSize,
    Paper,
    Machine,
    FinishingRate,
    Material,
    Product,
    ProductOption,
    QuoteRequest,
    QuoteItem,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = fields


class SheetSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SheetSize
        fields = ["id", "name", "width_mm", "height_mm"]


class PaperSerializer(serializers.ModelSerializer):
    sheet_size = SheetSizeSerializer(read_only=True)

    class Meta:
        model = Paper
        fields = [
            "id",
            "name",
            "sheet_size",
            "gsm",
            "price_per_sheet",
            "is_active",
        ]


class MachineSerializer(serializers.ModelSerializer):
    sheet_size = SheetSizeSerializer(read_only=True)

    class Meta:
        model = Machine
        fields = [
            "id",
            "name",
            "sheet_size",
            "gsm_min",
            "gsm_max",
            "cost_per_impression",
            "is_active",
        ]


class FinishingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinishingRate
        fields = ["id", "name", "rate_per_unit", "unit_label", "is_active"]


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ["id", "name", "price_per_unit", "unit_label", "is_active"]


class ProductOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOption
        fields = ["id", "paper", "machine", "finishing_rate", "material"]


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight for catalog listing."""

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "description", "is_active"]


class ProductCreateSerializer(serializers.ModelSerializer):
    """For seller creating products."""

    class Meta:
        model = Product
        fields = ["name", "slug", "description"]


class PaperCreateSerializer(serializers.ModelSerializer):
    """For seller creating paper."""

    class Meta:
        model = Paper
        fields = ["name", "sheet_size", "gsm", "price_per_sheet"]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full product with allowed options."""
    allowed_options = ProductOptionSerializer(many=True, read_only=True)
    default_paper = PaperSerializer(read_only=True)
    default_machine = MachineSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "default_paper",
            "default_machine",
            "allowed_options",
            "is_active",
        ]


class ShopListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ["id", "name", "slug"]


class ShopDetailSerializer(serializers.ModelSerializer):
    products = ProductListSerializer(many=True, read_only=True)

    class Meta:
        model = Shop
        fields = ["id", "name", "slug", "products"]


# Quote serializers
class QuoteItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    paper = PaperSerializer(read_only=True)
    machine = MachineSerializer(read_only=True)
    finishing_rate = FinishingRateSerializer(read_only=True)
    material = MaterialSerializer(read_only=True)

    class Meta:
        model = QuoteItem
        fields = [
            "id",
            "product",
            "quantity",
            "paper",
            "machine",
            "finishing_rate",
            "finishing_quantity",
            "material",
            "material_quantity",
            "unit_price",
            "total_price",
        ]


class QuoteItemCreateSerializer(serializers.ModelSerializer):
    """For adding items to quote — requires direct FKs."""

    class Meta:
        model = QuoteItem
        fields = [
            "product",
            "quantity",
            "paper",
            "machine",
            "finishing_rate",
            "finishing_quantity",
            "material",
            "material_quantity",
        ]

    def validate(self, data):
        product = data["product"]
        shop = self.context.get("shop")
        if shop and product.shop_id != shop.pk:
            raise serializers.ValidationError("Product must belong to the quote's shop.")
        paper = data["paper"]
        machine = data["machine"]
        if paper.shop_id != product.shop_id or machine.shop_id != product.shop_id:
            raise serializers.ValidationError("Paper and machine must belong to the product's shop.")
        if paper.sheet_size_id != machine.sheet_size_id:
            raise serializers.ValidationError("Paper and machine must have matching sheet size.")
        # Optional gsm range check
        if machine.gsm_min and paper.gsm < machine.gsm_min:
            raise serializers.ValidationError("Paper gsm below machine minimum.")
        if machine.gsm_max and paper.gsm > machine.gsm_max:
            raise serializers.ValidationError("Paper gsm above machine maximum.")
        return data


class QuoteRequestSerializer(serializers.ModelSerializer):
    items = QuoteItemSerializer(many=True, read_only=True)

    class Meta:
        model = QuoteRequest
        fields = ["id", "shop", "buyer", "status", "items", "created_at", "updated_at"]
        read_only_fields = ["buyer", "status"]


class QuoteRequestCreateSerializer(serializers.ModelSerializer):
    """For creating quote request (buyer)."""

    class Meta:
        model = QuoteRequest
        fields = ["shop"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm", "first_name", "last_name"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords must match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
