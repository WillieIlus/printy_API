"""
Permissions: Buyers create quote requests only. Sellers manage catalog/pricing.
"""
from rest_framework import permissions


def user_owns_shop(user, shop):
    """User is the shop owner."""
    return shop.owner_id == user.pk


def user_can_manage_shop(user, shop):
    """User can manage shop (owner or future staff)."""
    return user_owns_shop(user, shop)


class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Sellers (shop owners) can create/edit. Others read-only.
    Used for shop resources: products, paper, machines, etc.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        shop = getattr(obj, "shop", None)
        if shop and user_can_manage_shop(request.user, shop):
            return True
        return False


class IsShopOwner(permissions.BasePermission):
    """Only shop owner can perform action."""

    def has_object_permission(self, request, view, obj):
        shop = getattr(obj, "shop", None) or obj
        return user_can_manage_shop(request.user, shop)


class IsQuoteBuyerOrSeller(permissions.BasePermission):
    """
    Buyer can view/edit own quote (draft). Seller can view/price/send.
    """

    def has_object_permission(self, request, view, obj):
        if obj.buyer_id == request.user.pk:
            return True
        if user_can_manage_shop(request.user, obj.shop):
            return True
        return False


class BuyerCanCreateQuote(permissions.BasePermission):
    """Any authenticated user can create quote requests (buyer flow)."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
