"""
Common permissions for Printy API.
Shop-scoped access control.
"""
from rest_framework import permissions


class IsSellerOfShop(permissions.BasePermission):
    """Allow only shop owner (seller) to perform action."""

    def has_object_permission(self, request, view, obj):
        # obj is Shop
        if hasattr(obj, "owner"):
            return request.user == obj.owner
        # obj has shop (Machine, Paper, etc.)
        shop = getattr(obj, "shop", None)
        if shop is None:
            return False
        return request.user == shop.owner

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return True


class IsQuoteOwnerOrSeller(permissions.BasePermission):
    """Buyer can access own quotes; seller can access quotes of own shop."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        # Seller: shop owner
        if hasattr(obj, "shop") and request.user == obj.shop.owner:
            return True
        # Buyer: created the quote or is the customer
        if hasattr(obj, "created_by") and obj.created_by == request.user:
            return True
        return False

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


def get_shop_from_request(request):
    """Extract shop from view kwargs (shop_id) or object."""
    shop_id = request.resolver_match.kwargs.get("shop_id")
    if shop_id:
        from shops.models import Shop
        return Shop.objects.filter(pk=shop_id).first()
    return None


def user_owns_shop(user, shop):
    """Check if user is the shop owner."""
    return shop and user == shop.owner
