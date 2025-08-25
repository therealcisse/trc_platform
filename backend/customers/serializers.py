from typing import Any

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import ApiToken, InviteCode

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    invite_code = serializers.CharField()

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise ValidationError("email_exists")
        return value.lower()

    def validate_invite_code(self, value: str) -> str:
        try:
            invite = InviteCode.objects.get(code=value)
            if not invite.is_valid:
                if invite.used_by:
                    raise ValidationError("invite_used")
                elif invite.is_expired:
                    raise ValidationError("invite_expired")
                else:
                    raise ValidationError("invalid_invite")
        except InviteCode.DoesNotExist as e:
            raise ValidationError("invalid_invite") from e
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        invite_code = validated_data.pop("invite_code")
        invite = InviteCode.objects.get(code=invite_code)

        user = User.objects.create_user(
            email=validated_data["email"], password=validated_data["password"]
        )

        # Mark invite code as used
        invite.mark_as_used(user)

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        email = attrs.get("email", "").lower()
        password = attrs.get("password")

        user = authenticate(username=email, password=password)

        if not user:
            raise ValidationError("invalid_credentials")

        if not user.is_active:
            raise ValidationError("account_disabled")

        if not user.is_email_verified:
            raise ValidationError("email_not_verified")

        attrs["user"] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise ValidationError("incorrect_password")
        return value

    def save(self) -> None:
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()


class ApiTokenSerializer(serializers.ModelSerializer):
    token_once = serializers.CharField(read_only=True)

    class Meta:
        model = ApiToken
        fields = ["id", "name", "token_prefix", "token_once", "created_at"]
        read_only_fields = ["id", "token_prefix", "token_once", "created_at"]

    def create(self, validated_data: dict[str, Any]) -> ApiToken:
        user = self.context["request"].user

        # Generate token
        full_token, token_prefix, token_hash = ApiToken.generate_token()

        # Create token object
        token = ApiToken.objects.create(
            user=user, name=validated_data["name"], token_prefix=token_prefix, token_hash=token_hash
        )

        # Attach full token for one-time display
        token.token_once = full_token

        return token


class ApiTokenListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiToken
        fields = ["id", "name", "token_prefix", "created_at", "revoked_at", "last_used_at"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "is_active", "email_verified_at", "date_joined"]
        read_only_fields = fields
