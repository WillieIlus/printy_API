"""
Account views: JWT token obtain, refresh, register.
"""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import UserCreateSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Register a new user (buyer or seller)."""
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer


class MeView(generics.RetrieveAPIView):
    """Get current user profile."""
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
