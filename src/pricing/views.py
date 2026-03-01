"""
Pricing views. PrintingRate is machine-scoped.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import PrintingRate
from .serializers import PrintingRateSerializer
from inventory.models import Machine


class MachinePrintingRateViewSet(viewsets.ModelViewSet):
    """Seller: printing rates for a machine (machine belongs to seller's shop)."""
    permission_classes = [IsAuthenticated]
    serializer_class = PrintingRateSerializer

    def get_queryset(self):
        machine_id = self.kwargs.get("machine_id")
        return PrintingRate.objects.filter(
            machine_id=machine_id,
            machine__shop__owner=self.request.user,
        )

    def perform_create(self, serializer):
        machine = Machine.objects.get(
            pk=self.kwargs["machine_id"],
            shop__owner=self.request.user,
        )
        serializer.save(machine=machine)
