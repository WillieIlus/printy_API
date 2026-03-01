"""
Quote URL routing.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"quote-requests", views.QuoteRequestViewSet, basename="quote-request")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "quote-requests/<int:quote_request_pk>/items/",
        views.QuoteItemViewSet.as_view({"get": "list", "post": "create"}),
        name="quote-items-list",
    ),
    path(
        "quote-requests/<int:quote_request_pk>/items/<int:pk>/",
        views.QuoteItemViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="quote-items-detail",
    ),
]
