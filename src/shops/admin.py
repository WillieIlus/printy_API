"""
Shop admin cockpit with inlines for rapid setup.
"""
from django.contrib import admin
from .models import Shop
from inventory.models import Machine, Paper
from pricing.models import FinishingRate, Material


class MachineInline(admin.TabularInline):
    model = Machine
    extra = 1
    fields = ("name", "machine_type", "max_width_mm", "max_height_mm", "min_gsm", "max_gsm", "is_active")


class PaperInline(admin.TabularInline):
    model = Paper
    extra = 1
    fields = (
        "sheet_size", "gsm", "paper_type", "width_mm", "height_mm",
        "buying_price", "selling_price", "quantity_in_stock", "reorder_level", "is_active"
    )


class FinishingRateInline(admin.TabularInline):
    model = FinishingRate
    extra = 1
    fields = ("name", "charge_unit", "price", "setup_fee", "min_qty", "is_active")


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1
    fields = ("name", "unit", "buying_price", "selling_price", "is_active")


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "owner", "currency", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MachineInline, PaperInline, FinishingRateInline, MaterialInline]
