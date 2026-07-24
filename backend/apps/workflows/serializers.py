from rest_framework import serializers
from .models import DeleteRequest, RoleChangeRequest, AccessRequest, CreationRequest, EditRequest, ClarificationMessage
# ... [existing serializers here] ...
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
    user_role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = AccessRequest
        fields = [
            "id",
            "record_id",
            "user_id",
            "user_name",
            "user_role",
            "requested_access",
            "status",
            "created_at"
        ]


class CreationRequestSerializer(serializers.ModelSerializer):
    record_id = serializers.SerializerMethodField()
    record_name = serializers.SerializerMethodField()
    requested_by = serializers.CharField(source="requested_by.name", read_only=True)
    current_data = serializers.SerializerMethodField()
    has_unread = serializers.SerializerMethodField()

    class Meta:
        model = CreationRequest
        fields = [
            "id",
            "record_id",
            "record_name",
            "requested_by",
            "status",
            "current_data",
            "has_unread",
            "created_at"
        ]

    def get_has_unread(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        user = request.user
        if user.role in ['COMPLIANCE_OFFICER', 'ADMIN']:
            return obj.clarification_messages.exclude(sender__role='COMPLIANCE_OFFICER').filter(is_read=False).exists()
        else:
            return obj.clarification_messages.exclude(sender=user).filter(is_read=False).exists()

    def get_record_id(self, obj):
        if obj.record_public_id:
            return obj.record_public_id
        if obj.record:
            return obj.record.public_id
        return "Deleted Record"

    def get_record_name(self, obj):
        if obj.record_name:
            return obj.record_name
        if obj.record:
            return obj.record.name
        return "Deleted Record"

    def get_current_data(self, obj):
        if obj.record:
            from apps.records.serializers import RecordDetailSerializer
            return RecordDetailSerializer(obj.record, context=self.context).data
        return None


class EditRequestSerializer(serializers.ModelSerializer):
    record_id = serializers.CharField(source="record.public_id", read_only=True)
    requested_by = serializers.CharField(source="requested_by.name", read_only=True)
    current_data = serializers.SerializerMethodField()

    class Meta:
        model = EditRequest
        fields = [
            "id",
            "record_id",
            "requested_by",
            "status",
            "proposed_data",
            "current_data",
            "created_at"
        ]

    def get_current_data(self, obj):
        if obj.record:
            from apps.records.serializers import RecordDetailSerializer
            return RecordDetailSerializer(obj.record, context=self.context).data
        return None


class CreationAuditSerializer(serializers.ModelSerializer):
    record_id = serializers.SerializerMethodField()
    record_name = serializers.SerializerMethodField()
    requested_by = serializers.CharField(source="requested_by.name", read_only=True)
    reviewed_by = serializers.CharField(source="reviewed_by.name", read_only=True, default=None)

    class Meta:
        model = CreationRequest
        fields = [
            "id",
            "record_id",
            "record_name",
            "requested_by",
            "reviewed_by",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_record_id(self, obj):
        if obj.record_public_id:
            return obj.record_public_id
        if obj.record:
            return obj.record.public_id
        return "Deleted Record"

    def get_record_name(self, obj):
        if obj.record_name:
            return obj.record_name
        if obj.record:
            return obj.record.name
        return "Deleted Record"


class EditAuditSerializer(serializers.ModelSerializer):
    record_id = serializers.SerializerMethodField()
    record_name = serializers.SerializerMethodField()
    requested_by = serializers.CharField(source="requested_by.name", read_only=True)
    reviewed_by = serializers.CharField(source="reviewed_by.name", read_only=True, default=None)
    current_data = serializers.SerializerMethodField()

    class Meta:
        model = EditRequest
        fields = [
            "id",
            "record_id",
            "record_name",
            "requested_by",
            "reviewed_by",
            "status",
            "proposed_data",
            "current_data",
            "created_at",
            "updated_at",
        ]

    def get_record_id(self, obj):
        if obj.record_public_id:
            return obj.record_public_id
        if obj.record:
            return obj.record.public_id
        return "Deleted Record"

    def get_record_name(self, obj):
        if obj.record_name:
            return obj.record_name
        if obj.record:
            return obj.record.name
        return "Deleted Record"

    def get_current_data(self, obj):
        if obj.record:
            from apps.records.serializers import RecordDetailSerializer
            return RecordDetailSerializer(obj.record, context=self.context).data
        return None


class DeleteAuditSerializer(serializers.ModelSerializer):
    record_id = serializers.SerializerMethodField()
    record_name = serializers.SerializerMethodField()
    requested_by = serializers.CharField(source="requested_by.name", read_only=True)
    reviewed_by = serializers.CharField(source="reviewed_by.name", read_only=True, default=None)

    class Meta:
        model = DeleteRequest
        fields = [
            "id",
            "record_id",
            "record_name",
            "requested_by",
            "reviewed_by",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_record_id(self, obj):
        if obj.record_public_id:
            return obj.record_public_id
        if obj.record:
            return obj.record.public_id
        return "Deleted Record"

    def get_record_name(self, obj):
        if obj.record_name:
            return obj.record_name
        if obj.record:
            return obj.record.name
        return "Deleted Record"


class ClarificationMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.name", read_only=True)
    sender_role = serializers.CharField(source="sender.role", read_only=True)
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = ClarificationMessage
        fields = [
            "id",
            "sender_name",
            "sender_role",
            "message",
            "created_at",
            "is_me"
        ]

    def get_is_me(self, obj):
        request = self.context.get("request")
        if request and request.user:
            return obj.sender == request.user
        return False