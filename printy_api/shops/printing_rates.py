"""
Default printing rate templates for machines.
Apply when a machine is created (optional) via apply_default_printing_rates().
Can be called from views/serializers when creating a machine, or via the
apply_machine_printing_rates management command.
"""
from decimal import Decimal

from .models import Machine

# Default cost_per_impression and gsm range by sheet size name
DEFAULT_PRINTING_RATES = {
    "A4": {
        "cost_per_impression": Decimal("0.02"),
        "gsm_min": 80,
        "gsm_max": 400,
    },
    "A3": {
        "cost_per_impression": Decimal("0.04"),
        "gsm_min": 80,
        "gsm_max": 400,
    },
    "SRA3": {
        "cost_per_impression": Decimal("0.06"),
        "gsm_min": 80,
        "gsm_max": 350,
    },
}


def apply_default_printing_rates(machine: Machine) -> bool:
    """
    Apply default cost_per_impression and gsm_min/gsm_max to a machine
    based on its sheet_size. Returns True if rates were applied.
    """
    if not machine.sheet_size_id:
        return False

    template = DEFAULT_PRINTING_RATES.get(machine.sheet_size.name)
    if not template:
        return False

    machine.cost_per_impression = template["cost_per_impression"]
    machine.gsm_min = template.get("gsm_min")
    machine.gsm_max = template.get("gsm_max")
    machine.save(update_fields=["cost_per_impression", "gsm_min", "gsm_max"])
    return True
