from rest_framework import serializers
from .models import DeleteRequest, RoleChangeRequest, AccessRequest


class DeleteRequestSerializer(serializers.ModelSerializer):
    record_id = serializers.CharField(source="record.public_id", read_only=True)
    requested_by = serializers.CharField(source="requested_by.public_id", read_only=True)

    class Meta:
        model = DeleteRequest
        fields = [
            "id",
            "record_id",
            "requested_by",
            "status",
            "created_at"
        ]

class RoleChangeRequestSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="user.public_id", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = RoleChangeRequest
        fields = [
            "id",
            "user_id",
            "user_name",
            "requested_role",
            "status",
            "created_at"
        ]

class AccessRequestSerializer(serializers.ModelSerializer):
    record_id = serializers.CharField(source="record.public_id", read_only=True)
    user_id = serializers.CharField(source="user.public_id", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = AccessRequest
        fields = [
            "id",
            "record_id",
            "user_id",
            "user_name",
            "requested_access",
            "status",
            "created_at"
        ]