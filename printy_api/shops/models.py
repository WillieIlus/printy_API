"""
Printy API models — one concept = one model.
Shop-scoped resources. Quote items store direct FK refs (no lookup-by-attributes).
"""
from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user. Role determined by shop membership:
    - Seller: owns shop or is staff of shop
    - Buyer: creates quote requests (any authenticated user can be buyer)
    """
    pass


class Shop(models.Model):
    """Shop (seller's business). Owns all resources: paper, machines, materials, products."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_shops",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SheetSize(models.Model):
    """Standard sheet size (e.g. A4, SRA3). Used for Paper and Machine compatibility."""
    name = models.CharField(max_length=50, unique=True)
    width_mm = models.PositiveIntegerField()
    height_mm = models.PositiveIntegerField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.width_mm}x{self.height_mm}mm)"


class Paper(models.Model):
    """
    Paper stock. Shop-scoped. NO FK to Machine.
    Compatibility validated by sheet_size and optional gsm range.
    """
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="papers")
    name = models.CharField(max_length=200)
    sheet_size = models.ForeignKey(
        SheetSize,
        on_delete=models.PROTECT,
        related_name="papers",
    )
    gsm = models.PositiveIntegerField(help_text="Grams per square metre")
    price_per_sheet = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0"),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["shop", "name"]
        unique_together = [["shop", "name", "sheet_size", "gsm"]]

    def __str__(self):
        return f"{self.name} {self.sheet_size} {self.gsm}g"


class Machine(models.Model):
    """Print machine. Shop-scoped. Has sheet_size for Paper compatibility."""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="machines")
    name = models.CharField(max_length=200)
    sheet_size = models.ForeignKey(
        SheetSize,
        on_delete=models.PROTECT,
        related_name="machines",
    )
    gsm_min = models.PositiveIntegerField(null=True, blank=True)
    gsm_max = models.PositiveIntegerField(null=True, blank=True)
    cost_per_impression = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0"),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["shop", "name"]

    def __str__(self):
        return f"{self.name} ({self.sheet_size})"


class PrintingRate(models.Model):
    """Printing rate per machine (e.g. per impression). Allows multiple rates per machine."""
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name="printing_rates",
    )
    name = models.CharField(max_length=200, help_text="Rate label (e.g. Standard, Bulk)")
    cost_per_impression = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0"),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["machine", "name"]

    def __str__(self):
        return f"{self.machine.name} - {self.name}"


class FinishingRate(models.Model):
    """Finishing operation rate (e.g. cutting, folding). Shop-scoped."""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="finishing_rates")
    name = models.CharField(max_length=200)
    rate_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0"),
    )
    unit_label = models.CharField(max_length=50, default="unit")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["shop", "name"]

    def __str__(self):
        return f"{self.name} ({self.rate_per_unit}/{self.unit_label})"


class Material(models.Model):
    """Other material (e.g. ink, laminate). Shop-scoped."""
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="materials")
    name = models.CharField(max_length=200)
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0"),
    )
    unit_label = models.CharField(max_length=50, default="unit")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["shop", "name"]

    def __str__(self):
        return f"{self.name} ({self.price_per_unit}/{self.unit_label})"


class Product(models.Model):
    """
    Product/template. One system only (no parallel PrintTemplate vs ProductTemplate).
    Shop-scoped. Sellers manage; buyers only reference in quote requests.
    """
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    # Defaults for quote items; buyer can override within allowed options
    default_paper = models.ForeignKey(
        Paper,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products_default",
    )
    default_machine = models.ForeignKey(
        Machine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products_default",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["shop", "name"]
        unique_together = [["shop", "slug"]]

    def __str__(self):
        return self.name


class ProductOption(models.Model):
    """Allowed options for a product (paper, machine, finishing, material)."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="allowed_options",
    )
    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="product_options",
    )
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="product_options",
    )
    finishing_rate = models.ForeignKey(
        FinishingRate,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="product_options",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="product_options",
    )

    def __str__(self):
        parts = []
        if self.paper:
            parts.append(str(self.paper))
        if self.machine:
            parts.append(str(self.machine))
        if self.finishing_rate:
            parts.append(str(self.finishing_rate))
        if self.material:
            parts.append(str(self.material))
        return " | ".join(parts) or "Option"


class QuoteRequest(models.Model):
    """Quote request from buyer. Supports multiple items."""
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        PRICED = "priced", "Priced"
        SENT = "sent", "Sent"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="quote_requests")
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quote_requests",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Quote #{self.pk} ({self.status})"


class QuoteItem(models.Model):
    """
    Single item in a quote request.
    Stores direct FK refs to chosen Paper/Material/FinishingRate/Machine.
    NO lookup-by-attributes — avoids MultipleObjectsReturned.
    """
    quote_request = models.ForeignKey(
        QuoteRequest,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="quote_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    # Direct FKs — chosen at add-to-quote or pricing time
    paper = models.ForeignKey(
        Paper,
        on_delete=models.PROTECT,
        related_name="quote_items",
    )
    machine = models.ForeignKey(
        Machine,
        on_delete=models.PROTECT,
        related_name="quote_items",
    )
    finishing_rate = models.ForeignKey(
        FinishingRate,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="quote_items",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="quote_items",
    )
    finishing_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Units for finishing (e.g. cuts, folds)",
    )
    material_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("0"),
    )
    # Calculated prices (set by quote engine)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["quote_request", "pk"]

    def __str__(self):
        return f"{self.product} x{self.quantity}"
