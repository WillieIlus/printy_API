"""
Admin cockpit — shop resources with inlines for quick setup.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    Shop,
    SheetSize,
    Paper,
    Machine,
    PrintingRate,
    FinishingRate,
    Material,
    Product,
    ProductOption,
    QuoteRequest,
    QuoteItem,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_active"]


@admin.register(SheetSize)
class SheetSizeAdmin(admin.ModelAdmin):
    list_display = ["name", "width_mm", "height_mm"]
    search_fields = ["name"]


class PaperInline(admin.TabularInline):
    model = Paper
    extra = 1
    fields = ["name", "sheet_size", "gsm", "price_per_sheet", "is_active"]


class MachineInline(admin.TabularInline):
    model = Machine
    extra = 1
    fields = ["name", "sheet_size", "gsm_min", "gsm_max", "cost_per_impression", "is_active"]


class FinishingRateInline(admin.TabularInline):
    model = FinishingRate
    extra = 1
    fields = ["name", "rate_per_unit", "unit_label", "is_active"]


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1
    fields = ["name", "price_per_unit", "unit_label", "is_active"]


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "owner", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [
        MachineInline,
        PaperInline,
        FinishingRateInline,
        MaterialInline,
    ]
    raw_id_fields = ["owner"]


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ["name", "shop", "sheet_size", "gsm", "price_per_sheet", "is_active"]
    list_filter = ["shop", "is_active"]
    search_fields = ["name", "shop__name"]
    raw_id_fields = ["shop"]


class PrintingRateInline(admin.TabularInline):
    model = PrintingRate
    extra = 1
    fields = ["name", "cost_per_impression", "is_active"]


@admin.register(PrintingRate)
class PrintingRateAdmin(admin.ModelAdmin):
    list_display = ["name", "machine", "cost_per_impression", "is_active"]
    list_filter = ["machine__shop", "is_active"]
    search_fields = ["name", "machine__name"]
    raw_id_fields = ["machine"]


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ["name", "shop", "sheet_size", "cost_per_impression", "is_active"]
    list_filter = ["shop", "is_active"]
    search_fields = ["name", "shop__name"]
    raw_id_fields = ["shop"]
    inlines = [PrintingRateInline]


@admin.register(FinishingRate)
class FinishingRateAdmin(admin.ModelAdmin):
    list_display = ["name", "shop", "rate_per_unit", "unit_label", "is_active"]
    list_filter = ["shop", "is_active"]
    search_fields = ["name", "shop__name"]
    raw_id_fields = ["shop"]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ["name", "shop", "price_per_unit", "unit_label", "is_active"]
    list_filter = ["shop", "is_active"]
    search_fields = ["name", "shop__name"]
    raw_id_fields = ["shop"]


class ProductFinishingOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1
    fields = ["paper", "machine", "finishing_rate", "material"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "shop", "is_active", "created_at"]
    list_filter = ["shop", "is_active"]
    search_fields = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ["name"]}
    raw_id_fields = ["shop", "default_paper", "default_machine"]
    inlines = [ProductFinishingOptionInline]


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 0
    fields = [
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
    readonly_fields = ["unit_price", "total_price"]
    raw_id_fields = ["product", "paper", "machine", "finishing_rate", "material"]


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "shop", "buyer", "status", "created_at"]
    list_filter = ["shop", "status"]
    search_fields = ["buyer__username", "shop__name"]
    raw_id_fields = ["shop", "buyer"]
    inlines = [QuoteItemInline]


@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ["product", "quote_request", "quantity", "unit_price", "total_price"]
    list_filter = ["quote_request__shop"]
    search_fields = ["product__name", "quote_request__id"]
    raw_id_fields = ["quote_request", "product", "paper", "machine", "finishing_rate", "material"]
