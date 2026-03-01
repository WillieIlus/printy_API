"""
Account serializers.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation."""

    class Meta:
        model = User
        fields = ("id", "email", "name", "is_active", "is_staff")
        read_only_fields = fields


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "name")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
