"""
Inventory admin. MachineAdmin with PrintingRateInline.
"""
from django.contrib import admin

from .models import Machine, Paper
from pricing.models import PrintingRate


class PrintingRateInline(admin.TabularInline):
    model = PrintingRate
    extra = 1
    fields = ("sheet_size", "color_mode", "sides", "price", "is_active")


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "machine_type", "max_width_mm", "max_height_mm", "is_active")
    list_filter = ("shop", "is_active")
    search_fields = ("name",)
    inlines = [PrintingRateInline]


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("sheet_size", "gsm", "paper_type", "shop", "selling_price", "is_active")
    list_filter = ("shop", "sheet_size", "paper_type")
    search_fields = ("sheet_size", "paper_type")
