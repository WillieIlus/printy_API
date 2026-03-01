"""
Quotes admin.
"""
from django.contrib import admin

from .models import QuoteRequest, QuoteItem, QuoteItemFinishing


class QuoteItemFinishingInline(admin.TabularInline):
    model = QuoteItemFinishing
    extra = 0
    fields = ("finishing_rate", "coverage_qty", "price_override")


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 0
    fields = (
        "product", "quantity", "pricing_mode", "paper", "material",
        "chosen_width_mm", "chosen_height_mm", "sides", "color_mode", "machine",
        "unit_price", "line_total"
    )


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "customer_name", "status", "total", "created_at")
    list_filter = ("shop", "status")
    search_fields = ("customer_name", "customer_email")
    inlines = [QuoteItemInline]


@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ("id", "quote_request", "product", "quantity", "unit_price", "line_total")
    list_filter = ("quote_request__shop",)
    inlines = [QuoteItemFinishingInline]
