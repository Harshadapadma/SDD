from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserRole

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode


# -------------------------------
# Login Serializer
# -------------------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            request=self.context.get("request"),
            email=data.get("email"),
            password=data.get("password")
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("Account not activated")

        data["user"] = user
        return data


# -------------------------------
# Admin Create User Serializer
# -------------------------------
class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "name", "role"]

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            role=validated_data.get("role", UserRole.VIEWER)
        )

        user.is_active = False
        user.save()

        return user


# -------------------------------
# Set Password Serializer
# -------------------------------
class SetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data['uid']))
            user = User.objects.get(pk=uid)
        except:
            raise serializers.ValidationError("Invalid user")

        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError("Invalid or expired token")

        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        password = self.validated_data['password']

        user.set_password(password)
        user.is_active = True
        user.must_change_password = False
        user.is_email_verified = True
        user.save()

        return user


# -------------------------------
# User List Serializer
# -------------------------------
class UserListSerializer(serializers.ModelSerializer):
    is_profile_complete = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "public_id",
            "email",
            "name",
            "role",
            "is_active",
            "is_blacklisted",
            "is_profile_complete",
            "designation",
            "company_name",
            "mobile_number",
            "created_at"
        ]

# -------------------------------
# Profile Update Serializer
# -------------------------------
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "designation", "company_name", "mobile_number"]

# -------------------------------
# Change Password Serializer
# -------------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context.get("request").user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value