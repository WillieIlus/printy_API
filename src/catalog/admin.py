"""
Catalog admin. ProductAdmin with ProductFinishingOptionInline.
"""
from django.contrib import admin

from .models import Product, ProductFinishingOption


class ProductFinishingOptionInline(admin.TabularInline):
    model = ProductFinishingOption
    extra = 1
    fields = ("finishing_rate", "is_default", "price_adjustment")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "pricing_mode", "category", "is_active")
    list_filter = ("shop", "pricing_mode")
    search_fields = ("name", "category")
    inlines = [ProductFinishingOptionInline]
