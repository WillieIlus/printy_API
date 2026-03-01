"""
Quote views: buyer (own quotes, create, submit, items) and seller (price, send).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import QuoteRequest, QuoteItem
from .serializers import (
    QuoteRequestSerializer,
    QuoteRequestCreateSerializer,
    QuoteItemSerializer,
)
from .services import calculate_quote_request
from common.permissions import IsQuoteOwnerOrSeller


class QuoteRequestViewSet(viewsets.ModelViewSet):
    """Quote requests: list mine, create, retrieve, submit, price, send."""
    permission_classes = [IsAuthenticated, IsQuoteOwnerOrSeller]

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        return QuoteRequest.objects.filter(
            Q(created_by=user) | Q(shop__owner=user)
        ).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return QuoteRequestCreateSerializer
        return QuoteRequestSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        """Buyer: set status to SUBMITTED. Only when DRAFT."""
        quote = self.get_object()
        if quote.created_by != request.user:
            return Response({"detail": "Only the quote creator can submit."}, status=403)
        if quote.status != "DRAFT":
            return Response({"detail": "Only DRAFT quotes can be submitted."}, status=400)
        quote.status = "SUBMITTED"
        quote.save(update_fields=["status", "updated_at"])
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=["post"], url_path="price")
    def price(self, request, pk=None):
        """Seller: calculate & lock prices, set status PRICED."""
        quote = self.get_object()
        if quote.shop.owner != request.user:
            return Response({"detail": "Only shop owner can price quotes."}, status=403)
        if quote.status not in ("DRAFT", "SUBMITTED"):
            return Response({"detail": "Can only price DRAFT or SUBMITTED quotes."}, status=400)
        calculate_quote_request(quote, lock=True)
        quote.status = "PRICED"
        quote.save(update_fields=["status", "updated_at"])
        return Response(QuoteRequestSerializer(quote).data)

    @action(detail=True, methods=["post"], url_path="send")
    def send(self, request, pk=None):
        """Seller: set status SENT."""
        quote = self.get_object()
        if quote.shop.owner != request.user:
            return Response({"detail": "Only shop owner can send quotes."}, status=403)
        if quote.status != "PRICED":
            return Response({"detail": "Only PRICED quotes can be sent."}, status=400)
        quote.status = "SENT"
        quote.save(update_fields=["status", "updated_at"])
        return Response(QuoteRequestSerializer(quote).data)


class QuoteItemViewSet(viewsets.ModelViewSet):
    """Nested items: POST/PATCH/DELETE under quote. Only when DRAFT."""
    permission_classes = [IsAuthenticated]
    serializer_class = QuoteItemSerializer

    def _get_quote(self):
        from django.db.models import Q
        from rest_framework.exceptions import NotFound
        quote_id = self.kwargs.get("quote_request_pk")
        quote = QuoteRequest.objects.filter(
            Q(created_by=self.request.user) | Q(shop__owner=self.request.user)
        ).filter(pk=quote_id).first()
        if not quote:
            raise NotFound("Quote not found.")
        return quote

    def get_queryset(self):
        quote = self._get_quote()
        return QuoteItem.objects.filter(quote_request=quote)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["quote_request"] = self._get_quote()
        return ctx

    def perform_create(self, serializer):
        quote = self._get_quote()
        if quote.status != "DRAFT":
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot add items when quote is not DRAFT.")
        if quote.created_by != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only quote creator can add items.")
        serializer.save(quote_request=quote)

    def perform_update(self, serializer):
        quote = serializer.instance.quote_request
        if quote.status != "DRAFT":
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot edit items when quote is not DRAFT.")
        if quote.created_by != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only quote creator can edit items.")
        serializer.save()

    def perform_destroy(self, instance):
        quote = instance.quote_request
        if quote.status != "DRAFT":
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot delete items when quote is not DRAFT.")
        if quote.created_by != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only quote creator can delete items.")
        instance.delete()
