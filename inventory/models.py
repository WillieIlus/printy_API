from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampedModel
from shops.models import Shop

from .choices import MachineType, PaperType, SHEET_SIZE_DIMENSIONS, SheetSize


class Machine(TimeStampedModel):
    """Printing machine belonging to a shop."""

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="machines",
        verbose_name=_("shop"),
        help_text=_("Shop that owns this machine."),
    )
    name = models.CharField(
        max_length=255,
        default="",
        verbose_name=_("name"),
        help_text=_("Display name of the machine."),
    )
    machine_type = models.CharField(
        max_length=20,
        choices=MachineType.choices,
        default=MachineType.DIGITAL,
        verbose_name=_("machine type"),
        help_text=_("Type of printing machine (offset, digital, large format)."),
    )
    max_width_mm = models.PositiveIntegerField(
        verbose_name=_("max width (mm)"),
        help_text=_("Maximum printable width in millimeters."),
    )
    max_height_mm = models.PositiveIntegerField(
        verbose_name=_("max height (mm)"),
        help_text=_("Maximum printable height in millimeters."),
    )
    min_gsm = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("min GSM"),
        help_text=_("Minimum paper weight (grams per square metre) supported."),
    )
    max_gsm = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("max GSM"),
        help_text=_("Maximum paper weight (grams per square metre) supported."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("is active"),
        help_text=_("Whether the machine is active and available."),
    )

    class Meta:
        ordering = ["shop", "name"]
        verbose_name = _("machine")
        verbose_name_plural = _("machines")

    def __str__(self):
        return f"{self.name} ({self.shop.name})"


class Paper(TimeStampedModel):
    """
    Paper stock for SHEET printing (pre-cut sheets: A4, A3, SRA3, etc.).
    Tracks physical inventory (quantity_in_stock), buying/selling price per sheet.
    Not redundant with Material: Paper = sheet-fed; Material = large-format by area.
    """

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="papers",
        verbose_name=_("shop"),
        help_text=_("Shop that owns this paper stock."),
    )
    sheet_size = models.CharField(
        max_length=20,
        choices=SheetSize.choices,
        default=SheetSize.A4,
        verbose_name=_("sheet size"),
        help_text=_("Standard sheet size (A4, A3, SRA3, etc.)."),
    )
    gsm = models.PositiveIntegerField(
        verbose_name=_("GSM"),
        help_text=_("Paper weight in grams per square metre."),
    )
    paper_type = models.CharField(
        max_length=20,
        choices=PaperType.choices,
        default=PaperType.UNCOATED,
        verbose_name=_("paper type"),
        help_text=_("Type of paper (coated, uncoated, gloss, etc.)."),
    )
    width_mm = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("width (mm)"),
        help_text=_("Sheet width in millimeters (auto-filled from sheet size)."),
    )
    height_mm = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("height (mm)"),
        help_text=_("Sheet height in millimeters (auto-filled from sheet size)."),
    )
    buying_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("buying price"),
        help_text=_("Cost price per sheet."),
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("selling price"),
        help_text=_("Selling price per sheet."),
    )
    quantity_in_stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("quantity in stock"),
        help_text=_("Number of sheets currently in stock."),
    )
    reorder_level = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("reorder level"),
        help_text=_("Stock level that triggers reorder alert."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("is active"),
        help_text=_("Whether this paper stock is active."),
    )

    class Meta:
        ordering = ["shop", "sheet_size", "gsm", "paper_type"]
        verbose_name = _("paper")
        verbose_name_plural = _("papers")
        constraints = [
            models.UniqueConstraint(
                fields=["shop", "sheet_size", "gsm", "paper_type"],
                name="unique_shop_sheet_gsm_paper",
            )
        ]

    def __str__(self):
        return f"{self.sheet_size} {self.gsm}gsm {self.get_paper_type_display()}"

    def save(self, *args, **kwargs):
        # Auto-fill width_mm/height_mm from sheet_size when possible
        if self.sheet_size in SHEET_SIZE_DIMENSIONS and (
            self.width_mm is None or self.height_mm is None
        ):
            w, h = SHEET_SIZE_DIMENSIONS[self.sheet_size]
            if self.width_mm is None:
                self.width_mm = w
            if self.height_mm is None:
                self.height_mm = h
        super().save(*args, **kwargs)
