"""
URL configuration for printy_api project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from printy_api.health import health_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_view),
    path("api/", include("shops.urls")),
    path("api/", include("accounts.urls")),
    path("api/", include("quotes.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
