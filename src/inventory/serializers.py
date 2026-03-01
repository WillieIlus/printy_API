"""
Inventory serializers - used by shops views.
"""
from rest_framework import serializers

from .models import Machine, Paper


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = (
            "id", "name", "machine_type", "max_width_mm", "max_height_mm",
            "min_gsm", "max_gsm", "is_active"
        )


class PaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paper
        fields = (
            "id", "sheet_size", "gsm", "paper_type", "width_mm", "height_mm",
            "buying_price", "selling_price", "quantity_in_stock", "reorder_level", "is_active"
        )
