"""
URL configuration for Printy API.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("printy_api.shops.urls")),
]

# Shops urls will be added when views exist
