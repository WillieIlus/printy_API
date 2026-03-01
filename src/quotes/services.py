"""
Quote engine: calculate_quote_request.
Uses direct FK references only - no attribute-based lookups.
"""
from decimal import Decimal
from django.utils import timezone

from common.utils import decimal_from_value


def calculate_quote_request(quote_request, lock=False, force_recalc=False):
    """
    Calculate totals for all items in a quote request.
    If lock=True, persist unit_price, line_total, pricing_locked_at.
    """
    total = Decimal("0.00")

    for item in quote_request.items.select_related(
        "paper", "material", "machine", "product"
    ).prefetch_related("finishings__finishing_rate"):
        if item.pricing_locked_at and not force_recalc:
            if item.line_total is not None:
                total += item.line_total
            continue

        unit_price, line_total = _calculate_item(item)
        if unit_price is not None and line_total is not None:
            total += line_total

        if lock:
            item.unit_price = unit_price
            item.line_total = line_total
            item.pricing_locked_at = timezone.now()
            item.save(update_fields=["unit_price", "line_total", "pricing_locked_at", "updated_at"])

    if lock:
        quote_request.total = total
        quote_request.pricing_locked_at = timezone.now()
        quote_request.save(update_fields=["total", "pricing_locked_at", "updated_at"])

    return total


def _calculate_item(item):
    """Calculate unit_price and line_total for a single QuoteItem."""
    if item.pricing_mode == "SHEET":
        return _calculate_sheet_item(item)
    elif item.pricing_mode == "LARGE_FORMAT":
        return _calculate_large_format_item(item)
    return None, None


def _calculate_sheet_item(item):
    """SHEET: paper + printing + finishing."""
    if not item.paper:
        return None, None

    paper_cost = decimal_from_value(item.paper.selling_price)

    printing_cost = Decimal("0.00")
    if item.machine and item.sides and item.color_mode:
        from pricing.models import PrintingRate
        rate = PrintingRate.objects.filter(
            machine=item.machine,
            sheet_size=item.paper.sheet_size,
            color_mode=item.color_mode,
            sides=item.sides,
            is_active=True,
        ).first()
        if rate:
            printing_cost = decimal_from_value(rate.price)

    finishing_total = _calculate_finishing_for_item(item, is_sheet=True)
    finishing_per_unit = finishing_total / item.quantity if item.quantity else Decimal("0")

    unit_price = paper_cost + printing_cost + finishing_per_unit
    line_total = unit_price * item.quantity
    return unit_price, line_total


def _calculate_large_format_item(item):
    """LARGE_FORMAT: material * area + finishing."""
    if not item.material or not item.chosen_width_mm or not item.chosen_height_mm:
        return None, None

    w = decimal_from_value(item.chosen_width_mm) / 1000
    h = decimal_from_value(item.chosen_height_mm) / 1000
    area_sqm = w * h * item.quantity
    base = decimal_from_value(item.material.selling_price) * area_sqm

    finishing_total = _calculate_finishing_for_item(item, is_sheet=False, area_sqm=area_sqm)
    total = base + finishing_total
    unit_price = total / item.quantity if item.quantity else Decimal("0")
    line_total = total
    return unit_price, line_total


def _calculate_finishing_for_item(item, is_sheet=True, area_sqm=None):
    """Apply finishing rates by charge_unit. Uses direct FK to finishing_rate."""
    total = Decimal("0.00")
    quantity = item.quantity
    sides_count = 2 if item.sides == "DUPLEX" else 1

    for qif in item.finishings.select_related("finishing_rate"):
        fr = qif.finishing_rate
        price = decimal_from_value(qif.price_override) if qif.price_override is not None else decimal_from_value(fr.price)
        setup = decimal_from_value(fr.setup_fee) or Decimal("0")

        if fr.charge_unit == "PER_PIECE":
            total += price * quantity
        elif fr.charge_unit == "PER_SIDE":
            total += price * quantity * sides_count
        elif fr.charge_unit == "PER_SQM":
            if area_sqm is not None:
                total += price * area_sqm
            elif is_sheet and item.paper and item.paper.width_mm and item.paper.height_mm:
                sheet_sqm = (item.paper.width_mm / 1000) * (item.paper.height_mm / 1000)
                total += price * sheet_sqm * quantity
        elif fr.charge_unit == "FLAT":
            total += price + setup

    return total
