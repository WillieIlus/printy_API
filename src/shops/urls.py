"""
Shop URL routing.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from pricing.views import MachinePrintingRateViewSet

# Public routes (AllowAny)
public_router = DefaultRouter()
public_router.register(r"public/shops", views.PublicShopViewSet, basename="public-shop")

# Seller routes (auth required)
seller_router = DefaultRouter()
seller_router.register(r"shops", views.SellerShopViewSet, basename="seller-shop")

urlpatterns = [
    path("", include(public_router.urls)),
    path("", include(seller_router.urls)),
    path(
        "shops/<int:shop_id>/machines/",
        views.ShopMachineViewSet.as_view({"get": "list", "post": "create"}),
        name="shop-machines-list",
    ),
    path(
        "shops/<int:shop_id>/machines/<int:pk>/",
        views.ShopMachineViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="shop-machines-detail",
    ),
    path(
        "shops/<int:shop_id>/papers/",
        views.ShopPaperViewSet.as_view({"get": "list", "post": "create"}),
        name="shop-papers-list",
    ),
    path(
        "shops/<int:shop_id>/papers/<int:pk>/",
        views.ShopPaperViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="shop-papers-detail",
    ),
    path(
        "shops/<int:shop_id>/finishing-rates/",
        views.ShopFinishingRateViewSet.as_view({"get": "list", "post": "create"}),
        name="shop-finishing-rates-list",
    ),
    path(
        "shops/<int:shop_id>/finishing-rates/<int:pk>/",
        views.ShopFinishingRateViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="shop-finishing-rates-detail",
    ),
    path(
        "shops/<int:shop_id>/materials/",
        views.ShopMaterialViewSet.as_view({"get": "list", "post": "create"}),
        name="shop-materials-list",
    ),
    path(
        "shops/<int:shop_id>/materials/<int:pk>/",
        views.ShopMaterialViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="shop-materials-detail",
    ),
    path(
        "shops/<int:shop_id>/products/",
        views.ShopProductViewSet.as_view({"get": "list", "post": "create"}),
        name="shop-products-list",
    ),
    path(
        "shops/<int:shop_id>/products/<int:pk>/",
        views.ShopProductViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="shop-products-detail",
    ),
    path(
        "machines/<int:machine_id>/printing-rates/",
        MachinePrintingRateViewSet.as_view({"get": "list", "post": "create"}),
        name="machine-printing-rates-list",
    ),
    path(
        "machines/<int:machine_id>/printing-rates/<int:pk>/",
        MachinePrintingRateViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="machine-printing-rates-detail",
    ),
]
