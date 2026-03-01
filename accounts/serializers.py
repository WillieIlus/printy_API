from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """User profile with editable preferred_language."""

    class Meta:
        model = User
        fields = ["id", "email", "name", "preferred_language", "is_active", "is_staff"]
        read_only_fields = ["id", "email", "is_active", "is_staff"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password", "name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Token serializer that accepts email for login (email-based auth)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)
        self.fields["email"] = serializers.EmailField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get("email", "").strip()
        password = attrs.get("password")

        if not email:
            raise serializers.ValidationError({"email": "Email is required."})

        from django.contrib.auth import authenticate

        request = self.context.get("request")
        self.user = authenticate(
            request=request, username=email, password=password
        )
        if self.user is None:
            self.user = User.objects.filter(email=email).first()
            if self.user and not self.user.check_password(password):
                self.user = None

        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise serializers.ValidationError(
                {"detail": "No active account found with the given credentials."}
            )

        refresh = self.get_token(self.user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        if api_settings.UPDATE_LAST_LOGIN:
            from django.contrib.auth.models import update_last_login

            update_last_login(None, self.user)

        return data
