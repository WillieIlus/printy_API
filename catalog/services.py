"""
Product price range calculation.
Returns "From KES X" / "Up to KES Y" or structured missing_fields when data is incomplete.
Uses sensible defaults: quantity = min_quantity (default 1); size = default size if present.
"""
from decimal import Decimal
from math import ceil

from django.db.models import Q

from catalog.choices import PricingMode
from catalog.models import Product
from inventory.choices import MachineType, SheetSize, SHEET_SIZE_DIMENSIONS
from inventory.models import Machine, Paper
from pricing.choices import ColorMode, Sides
from pricing.models import Material, PrintingRate
from quotes.diagnostics import build_product_diagnostics


# Lay-person friendly pricing mode labels and explanations
PRICING_MODE_LABELS = {
    PricingMode.SHEET: "Sheet",
    PricingMode.LARGE_FORMAT: "Large format",
}
PRICING_MODE_EXPLANATIONS = {
    PricingMode.SHEET: "Charged per sheet. Price depends on paper type, single/double-sided printing, and quantity.",
    PricingMode.LARGE_FORMAT: "Charged by area (per sqm). Price depends on material (vinyl, banner, etc.) and dimensions.",
}


def _format_price_display(min_val, max_val, can_calculate) -> str:
    """Human-readable price string for cards."""
    if not can_calculate:
        return "Price on request"
    if min_val is None:
        return "Price on request"
    min_f = float(min_val)
    max_f = float(max_val) if max_val is not None else None
    if max_f is None or abs(max_f - min_f) < 0.01:
        return f"From KES {min_f:,.0f}"
    return f"KES {min_f:,.0f} – {max_f:,.0f}"


def product_price_hint(product: Product) -> dict:
    """
    Compute price hint for product list display.
    Returns a clean structure: price_display (human-readable), pricing_mode_label, pricing_mode_explanation,
    and only non-empty diagnostic fields when can_calculate is False.
    """
    result = get_product_price_range(product)
    min_val = result["lowest_price"]
    max_val = result["highest_price"]
    missing = result["missing_fields"]
    can_calculate = result["can_calculate"]
    diag = build_product_diagnostics(product, missing)

    out = {
        "can_calculate": can_calculate,
        "min_price": float(min_val) if min_val is not None else None,
        "max_price": float(max_val) if max_val is not None else None,
        "price_display": _format_price_display(min_val, max_val, can_calculate),
        "pricing_mode_label": PRICING_MODE_LABELS.get(product.pricing_mode, product.pricing_mode or "—"),
        "pricing_mode_explanation": PRICING_MODE_EXPLANATIONS.get(
            product.pricing_mode,
            "Price depends on your choices (paper, quantity, finishing).",
        ),
    }
    # Only include diagnostic fields when we cannot calculate
    if not can_calculate:
        out["reason"] = diag["reason"] or "More details needed to calculate price."
        if missing:
            out["missing_fields"] = missing
        if diag["suggestions"]:
            out["suggestions"] = diag["suggestions"]
    return out


def compute_product_price_range_est(product: Product) -> dict:
    """
    Compute price range estimate for SHEET products.
    Lowest = paper that minimizes unit_price_est; Highest = paper that maximizes it.
    Returns structure for price_range_est serializer field.
    """
    shop = product.shop
    min_qty = getattr(product, "min_quantity", 1) or 1
    color_mode = ColorMode.COLOR
    sides = getattr(product, "default_sides", Sides.SIMPLEX) or Sides.SIMPLEX
    sheets_used = 1  # Start with 1 for range display unless dimensions available

    if product.pricing_mode != PricingMode.SHEET:
        return {
            "can_calculate": False,
            "price_display": "Price on request",
            "pricing_mode_label": PRICING_MODE_LABELS.get(product.pricing_mode, str(product.pricing_mode or "—")),
            "pricing_mode_explanation": PRICING_MODE_EXPLANATIONS.get(
                product.pricing_mode,
                "Price depends on your choices (paper, quantity, finishing).",
            ),
            "lowest": _empty_range_payload(),
            "highest": _empty_range_payload(),
            "reason": "Price range applies to sheet products only.",
            "suggestions": [
                {"code": "SET_PRICING_MODE", "message": "Price range est. applies to Sheet products only."},
            ],
        }

    missing = []
    suggestions = []

    # Infer sheet_size: product.default_sheet_size, or SRA3 for digital, else first from shop papers
    sheet_size = (getattr(product, "default_sheet_size", None) or "").strip()
    if not sheet_size:
        papers_any = list(Paper.objects.filter(shop=shop, is_active=True, selling_price__gt=0).values_list("sheet_size", flat=True).distinct())
        digital_machines = Machine.objects.filter(shop=shop, is_active=True, machine_type=MachineType.DIGITAL).exists()
        if digital_machines and SheetSize.SRA3 in papers_any:
            sheet_size = SheetSize.SRA3
        elif papers_any:
            sheet_size = papers_any[0]
        else:
            sheet_size = SheetSize.SRA3  # Default fallback

    # Eligible papers: shop, sheet_size, selling_price > 0, gsm range
    papers_qs = Paper.objects.filter(
        shop=shop,
        is_active=True,
        selling_price__gt=0,
        sheet_size=sheet_size,
    )
    if product.min_gsm is not None:
        papers_qs = papers_qs.filter(gsm__gte=product.min_gsm)
    if product.max_gsm is not None:
        papers_qs = papers_qs.filter(gsm__lte=product.max_gsm)
    eligible_papers = list(papers_qs)

    if not eligible_papers:
        missing.append("paper")
        suggestions.append({
            "code": "ADD_PAPER",
            "message": f"Add paper selling prices for {sheet_size} papers under Shop → Papers.",
        })

    # Machine: first active that supports sheet size (fits sw×sh or sh×sw)
    sheet_dims = SHEET_SIZE_DIMENSIONS.get(sheet_size, (0, 0))
    sw, sh = sheet_dims
    sheet_fits = (Q(max_width_mm__gte=sw) & Q(max_height_mm__gte=sh)) | (Q(max_width_mm__gte=sh) & Q(max_height_mm__gte=sw))
    machine = Machine.objects.filter(shop=shop, is_active=True).filter(sheet_fits).first()
    if not machine:
        machine = Machine.objects.filter(shop=shop, is_active=True).first()
    if not machine:
        missing.append("machine")
        suggestions.append({
            "code": "ADD_MACHINE",
            "message": "Add a machine under Shop → Machines.",
        })

    # Printing rate
    rate, print_price = None, None
    if machine:
        rate, print_price = PrintingRate.resolve(machine, sheet_size, color_mode, sides)
    if not rate or print_price is None:
        missing.append("printing_rate")
        machine_name = machine.name if machine else "machine"
        suggestions.append({
            "code": "ADD_PRINTING_RATE",
            "message": f"Set {machine_name} single/double printing rates under Machine → Printing Rates.",
        })

    if missing:
        return {
            "can_calculate": False,
            "price_display": "Price on request",
            "pricing_mode_label": PRICING_MODE_LABELS.get(product.pricing_mode, str(product.pricing_mode or "—")),
            "pricing_mode_explanation": PRICING_MODE_EXPLANATIONS.get(
                product.pricing_mode,
                "Price depends on your choices (paper, quantity, finishing).",
            ),
            "lowest": _empty_range_payload(),
            "highest": _empty_range_payload(),
            "reason": "Shop needs to add paper, machine, or printing rates to show prices.",
            "missing_fields": missing,
            "suggestions": suggestions,
        }

    # Compute unit_price_est for each eligible paper; select min and max
    assumptions = {
        "quantity_used": min_qty,
        "sheet_size": sheet_size,
        "color_mode": color_mode,
        "sides": sides,
        "sheets_used": sheets_used,
    }

    paper_costs = []
    for paper in eligible_papers:
        unit_price_est = float(paper.selling_price) + float(print_price)
        total_est = unit_price_est * sheets_used
        paper_label = f"{paper.sheet_size} {paper.gsm}gsm {paper.get_paper_type_display()}"
        paper_costs.append({
            "paper": paper,
            "unit_price_est": unit_price_est,
            "total_est": total_est,
            "paper_label": paper_label,
        })

    paper_costs.sort(key=lambda x: x["unit_price_est"])
    lowest_data = paper_costs[0]
    highest_data = paper_costs[-1]

    currency = getattr(shop, "currency", "KES") or "KES"

    def build_payload(data, prefix):
        p = data["paper"]
        u = data["unit_price_est"]
        t = data["total_est"]
        return {
            "total": t,
            "unit_price": u,
            "paper_id": p.id,
            "paper_label": data["paper_label"],
            "printing_rate_id": rate.id if rate else None,
            "assumptions": assumptions,
            "summary": f"{prefix} based on {data['paper_label']} (KES {p.selling_price:,.0f}) + {machine.name} {'double' if sides == Sides.DUPLEX else 'single'} (KES {print_price:,.0f}) = KES {u:,.0f} per sheet.",
        }

    low_payload = build_payload(lowest_data, "Lowest")
    high_payload = build_payload(highest_data, "Highest")
    low_total = low_payload["total"]
    high_total = high_payload["total"]
    price_display = _format_price_display(low_total, high_total, True) if (low_total and high_total) else "Price on request"

    return {
        "can_calculate": True,
        "price_display": price_display,
        "pricing_mode_label": PRICING_MODE_LABELS.get(PricingMode.SHEET, "Sheet"),
        "pricing_mode_explanation": PRICING_MODE_EXPLANATIONS.get(
            PricingMode.SHEET,
            "Charged per sheet. Price depends on paper type, single/double-sided printing, and quantity.",
        ),
        "lowest": low_payload,
        "highest": high_payload,
    }


def _empty_range_payload():
    return {
        "total": None,
        "unit_price": None,
        "paper_id": None,
        "paper_label": None,
        "printing_rate_id": None,
        "assumptions": {},
        "summary": None,
    }


def get_product_price_range(product: Product) -> dict:
    """
    Compute price range for a product.
    Returns:
        {
            "lowest_price": Decimal | None,
            "highest_price": Decimal | None,
            "can_calculate": bool,
            "missing_fields": list[str],
        }
    """
    missing = []
    shop = product.shop
    min_qty = getattr(product, "min_quantity", 1) or 1

    if product.pricing_mode == PricingMode.SHEET:
        # Need: dimensions, paper, machine, printing rate
        if not product.default_finished_width_mm or not product.default_finished_height_mm:
            missing.append("dimensions")
        papers = list(Paper.objects.filter(shop=shop, is_active=True, selling_price__gt=0))
        if not papers:
            missing.append("paper")
        machines = list(Machine.objects.filter(shop=shop, is_active=True))
        if not machines:
            missing.append("machine")

        if missing:
            return {
                "lowest_price": None,
                "highest_price": None,
                "can_calculate": False,
                "missing_fields": missing,
            }

        # Find cheapest and most expensive combinations
        low_total = Decimal("999999")
        high_total = Decimal("0")

        for paper in papers:
            if not paper.selling_price or not paper.width_mm or not paper.height_mm:
                continue
            cps = product.get_copies_per_sheet(paper.sheet_size, paper.width_mm, paper.height_mm)
            if cps <= 0:
                continue
            sheets = ceil(min_qty / cps)

            for machine in machines:
                for color in [ColorMode.BW, ColorMode.COLOR]:
                    for sides in [Sides.SIMPLEX, Sides.DUPLEX]:
                        rate, price = PrintingRate.resolve(
                            machine, paper.sheet_size, color, sides
                        )
                        if rate and price is not None:
                            paper_cost = paper.selling_price * sheets
                            print_cost = price * sheets
                            total = paper_cost + print_cost
                            low_total = min(low_total, total)
                            high_total = max(high_total, total)

        if low_total == Decimal("999999"):
            missing.append("printing_rate")
            return {
                "lowest_price": None,
                "highest_price": None,
                "can_calculate": False,
                "missing_fields": missing,
            }

        return {
            "lowest_price": low_total if low_total < Decimal("999999") else None,
            "highest_price": high_total if high_total > 0 else None,
            "can_calculate": True,
            "missing_fields": [],
        }

    elif product.pricing_mode == PricingMode.LARGE_FORMAT:
        materials = list(Material.objects.filter(shop=shop, is_active=True, selling_price__gt=0))
        if not materials:
            missing.append("material")

        w_mm = getattr(product, "min_width_mm", None) or product.default_finished_width_mm
        h_mm = getattr(product, "min_height_mm", None) or product.default_finished_height_mm
        if not w_mm or not h_mm:
            missing.append("dimensions")

        if missing:
            return {
                "lowest_price": None,
                "highest_price": None,
                "can_calculate": False,
                "missing_fields": missing,
            }

        area_sqm = (Decimal(w_mm) / 1000) * (Decimal(h_mm) / 1000) * min_qty
        low_total = Decimal("999999")
        high_total = Decimal("0")
        for mat in materials:
            total = mat.selling_price * area_sqm
            low_total = min(low_total, total)
            high_total = max(high_total, total)

        return {
            "lowest_price": low_total if low_total < Decimal("999999") else None,
            "highest_price": high_total if high_total > 0 else None,
            "can_calculate": True,
            "missing_fields": [],
        }

    return {
        "lowest_price": None,
        "highest_price": None,
        "can_calculate": False,
        "missing_fields": ["pricing_mode"],
    }


def update_product_price_range(product: Product) -> None:
    """Update product.lowest_price and highest_price from calculation."""
    result = get_product_price_range(product)
    if result["can_calculate"]:
        product.lowest_price = result["lowest_price"]
        product.highest_price = result["highest_price"]
        product.save(update_fields=["lowest_price", "highest_price", "updated_at"])
