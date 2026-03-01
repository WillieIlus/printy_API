"""
Quote engine — calculates prices using direct FK refs. NO lookup-by-attributes.
"""
from decimal import Decimal

from .models import QuoteItem, QuoteRequest


def calculate_quote_item(item: QuoteItem) -> tuple[Decimal, Decimal]:
    """
    Calculate unit_price and total_price for a QuoteItem.
    Uses direct FKs only — no attribute lookups.
    """
    paper = item.paper
    machine = item.machine
    quantity = item.quantity

    # Paper cost: sheets needed (simplified: 1 sheet per unit for now)
    # Real logic may vary (e.g. imposition); this is a baseline
    sheets_needed = quantity
    paper_cost = paper.price_per_sheet * sheets_needed

    # Machine cost: impressions
    impressions = quantity
    machine_cost = machine.cost_per_impression * impressions

    # Finishing
    finishing_cost = Decimal("0")
    if item.finishing_rate and item.finishing_quantity:
        finishing_cost = (
            item.finishing_rate.rate_per_unit * item.finishing_quantity
        )

    # Material
    material_cost = Decimal("0")
    if item.material and item.material_quantity:
        material_cost = item.material.price_per_unit * item.material_quantity

    total = paper_cost + machine_cost + finishing_cost + material_cost
    unit_price = total / quantity if quantity else Decimal("0")

    return unit_price, total


def recalculate_quote_request(quote_request: QuoteRequest, force: bool = False) -> None:
    """
    Recalculate all items in a quote request and save.
    When quote is PRICED, prices are locked; recalc is skipped unless force=True.
    """
    if quote_request.status == QuoteRequest.Status.PRICED and not force:
        return
    for item in quote_request.items.all():
        unit_price, total_price = calculate_quote_item(item)
        item.unit_price = unit_price
        item.total_price = total_price
        item.save()
