"""
Shop views: public (AllowAny) and seller (auth).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Shop
from .serializers import (
    ShopListSerializer,
    ShopDetailSerializer,
    ShopCatalogSerializer,
    MachineSerializer,
    PaperSerializer,
    FinishingRateSerializer,
    MaterialSerializer,
    ProductCatalogSerializer,
)
from inventory.models import Machine, Paper
from pricing.models import FinishingRate, Material
from catalog.models import Product
from common.permissions import IsSellerOfShop


class PublicShopViewSet(viewsets.ReadOnlyModelViewSet):
    """Public: list active shops, get catalog by slug."""
    permission_classes = [AllowAny]
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        return Shop.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == "catalog":
            return ShopCatalogSerializer
        return ShopListSerializer

    @action(detail=True, url_path="catalog", methods=["get"])
    def catalog(self, request, slug=None):
        """GET /api/public/shops/{slug}/catalog/ - list products + finishing options."""
        shop = self.get_object()
        products = Product.objects.filter(shop=shop, is_active=True).prefetch_related(
            "finishing_options__finishing_rate"
        )
        serializer = ProductCatalogSerializer(products, many=True)
        return Response({"shop": {"id": shop.id, "name": shop.name, "slug": shop.slug}, "products": serializer.data})


class SellerShopViewSet(viewsets.ModelViewSet):
    """Seller: manage own shop only."""
    permission_classes = [IsAuthenticated, IsSellerOfShop]
    serializer_class = ShopDetailSerializer

    def get_queryset(self):
        return Shop.objects.filter(owner=self.request.user)


class ShopMachineViewSet(viewsets.ModelViewSet):
    """Seller: machines for a shop."""
    permission_classes = [IsAuthenticated]
    serializer_class = MachineSerializer

    def get_queryset(self):
        shop_id = self.kwargs.get("shop_id")
        return Machine.objects.filter(shop_id=shop_id, shop__owner=self.request.user)

    def perform_create(self, serializer):
        from .models import Shop
        shop = Shop.objects.get(pk=self.kwargs["shop_id"], owner=self.request.user)
        serializer.save(shop=shop)


class ShopPaperViewSet(viewsets.ModelViewSet):
    """Seller: papers for a shop."""
    permission_classes = [IsAuthenticated]
    serializer_class = PaperSerializer

    def get_queryset(self):
        shop_id = self.kwargs.get("shop_id")
        return Paper.objects.filter(shop_id=shop_id, shop__owner=self.request.user)

    def perform_create(self, serializer):
        from .models import Shop
        shop = Shop.objects.get(pk=self.kwargs["shop_id"], owner=self.request.user)
        serializer.save(shop=shop)


class ShopFinishingRateViewSet(viewsets.ModelViewSet):
    """Seller: finishing rates for a shop."""
    permission_classes = [IsAuthenticated]
    serializer_class = FinishingRateSerializer

    def get_queryset(self):
        shop_id = self.kwargs.get("shop_id")
        return FinishingRate.objects.filter(shop_id=shop_id, shop__owner=self.request.user)

    def perform_create(self, serializer):
        from .models import Shop
        shop = Shop.objects.get(pk=self.kwargs["shop_id"], owner=self.request.user)
        serializer.save(shop=shop)


class ShopMaterialViewSet(viewsets.ModelViewSet):
    """Seller: materials for a shop."""
    permission_classes = [IsAuthenticated]
    serializer_class = MaterialSerializer

    def get_queryset(self):
        shop_id = self.kwargs.get("shop_id")
        return Material.objects.filter(shop_id=shop_id, shop__owner=self.request.user)

    def perform_create(self, serializer):
        from .models import Shop
        shop = Shop.objects.get(pk=self.kwargs["shop_id"], owner=self.request.user)
        serializer.save(shop=shop)


class ShopProductViewSet(viewsets.ModelViewSet):
    """Seller: products for a shop."""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from catalog.serializers import ProductSerializer
        return ProductSerializer

    def get_queryset(self):
        shop_id = self.kwargs.get("shop_id")
        return Product.objects.filter(shop_id=shop_id, shop__owner=self.request.user)

    def perform_create(self, serializer):
        from .models import Shop
        shop = Shop.objects.get(pk=self.kwargs["shop_id"], owner=self.request.user)
        serializer.save(shop=shop)
