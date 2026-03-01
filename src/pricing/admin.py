"""
Pricing admin. Models also inlined under Shop.
"""
from django.contrib import admin

from .models import PrintingRate, FinishingRate, Material


@admin.register(FinishingRate)
class FinishingRateAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "charge_unit", "price", "is_active")
    list_filter = ("shop", "charge_unit")


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "unit", "selling_price", "is_active")
    list_filter = ("shop",)


@admin.register(PrintingRate)
class PrintingRateAdmin(admin.ModelAdmin):
    list_display = ("machine", "sheet_size", "color_mode", "sides", "price", "is_active")
    list_filter = ("machine", "color_mode", "sides")
