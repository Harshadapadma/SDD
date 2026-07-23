import re
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserRole

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode


# -------------------------------
# Shared Password Strength Validator
# -------------------------------
def validate_password_strength(password):
    """
    Enforces: min 8 chars, at least 1 uppercase letter,
    at least 1 digit, and at least 1 special character.
    """
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number.")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
        errors.append("Password must contain at least one special character.")
    if errors:
        raise serializers.ValidationError(errors)
    return password


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

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        if not re.match(r"^[a-zA-Z\s\.\-\']+$", value):
            raise serializers.ValidationError("Name must contain only letters, spaces, dots, hyphens, and single quotes.")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", value):
            raise serializers.ValidationError("Enter a valid email address.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value

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

    def validate_password(self, value):
        return validate_password_strength(value)

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
    records_access = serializers.SerializerMethodField()

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
            "created_at",
            "records_access"
        ]

    def get_records_access(self, obj):
        from apps.records.models import RecordAccess
        accesses = RecordAccess.objects.filter(user=obj).select_related('record')
        return [
            {
                "record_id": a.record.public_id,
                "record_name": a.record.name,
                "pan": a.record.pan,
                "source_company": a.record.source_company,
                "access_type": "VIEW" if obj.role == "VIEWER" else a.access_type
            }
            for a in accesses
        ]

# -------------------------------
# Profile Update Serializer
# -------------------------------
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "designation", "company_name", "mobile_number"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        if not re.match(r"^[a-zA-Z\s\.\-\']+$", value):
            raise serializers.ValidationError("Name must contain only letters, spaces, dots, hyphens, and single quotes.")
        return value

    def validate_designation(self, value):
        if value:
            value = value.strip()
            if value and len(value) < 2:
                raise serializers.ValidationError("Designation must be at least 2 characters long.")
        return value

    def validate_company_name(self, value):
        if value:
            value = value.strip()
            if value and len(value) < 2:
                raise serializers.ValidationError("Company name must be at least 2 characters long.")
        return value

    def validate_mobile_number(self, value):
        if value:
            value = value.strip()
            if value:
                if not re.match(r"^\d{10}$", value):
                    raise serializers.ValidationError("Mobile number must be exactly 10 digits.")
        return value

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

    def validate_new_password(self, value):
        return validate_password_strength(value)