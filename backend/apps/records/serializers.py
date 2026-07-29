import re
from rest_framework import serializers
from .models import Record


# -------------------------------
# Create Record Serializer
# -------------------------------
class RecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = [
            "name",
            "designation",
            "employee_code",
            "pan",
            "source_company",
            "info_details",
            "info_received_date",
            "disclosure_name",
            "disclosure_designation",
            "disclosure_department",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        if not re.match(r"^[a-zA-Z\s\.\-\']+$", value):
            raise serializers.ValidationError("Name must contain only letters, spaces, dots, hyphens, and single quotes.")
        return value

    def validate_disclosure_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Disclosure name cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("Disclosure name must be at least 2 characters long.")
        if not re.match(r"^[a-zA-Z\s\.\-\']+$", value):
            raise serializers.ValidationError("Disclosure name must contain only letters, spaces, dots, hyphens, and single quotes.")
        return value

    def validate_designation(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Designation cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("Designation must be at least 2 characters long.")
        return value

    def validate_disclosure_designation(self, value):
        if value is None:
            return ""
        return value.strip()

    def validate_disclosure_department(self, value):
        if value is None:
            return ""
        return value.strip()

    def validate_source_company(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Source company cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("Source company must be at least 2 characters long.")
        return value

    def validate_employee_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Employee code cannot be empty.")
        if len(value) < 2:
            raise serializers.ValidationError("Employee code must be at least 2 characters long.")
        if not re.match(r"^[a-zA-Z0-9\-\/]+$", value):
            raise serializers.ValidationError("Employee code must contain only letters, numbers, hyphens, and slashes.")
        return value

    def validate_pan(self, value):
        value = value.strip().upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", value):
            raise serializers.ValidationError("PAN must be in standard Indian format (e.g. ABCDE1234F).")
        return value

    def validate_info_received_date(self, value):
        from django.utils import timezone
        if value > timezone.localdate():
            raise serializers.ValidationError("Date received cannot be in the future.")
        return value

    def validate_info_details(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Information details cannot be empty.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user

        record = Record.objects.create(
            created_by=user,
            updated_by=user,
            **validated_data
        )

        # Give creator EDIT access by default
        from .models import RecordAccess
        RecordAccess.objects.create(
            user=user,
            record=record,
            access_type="EDIT",
            assigned_by=user
        )

        return record
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


# -------------------------------
# List Record Serializer
# -------------------------------
class RecordListSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.public_id")
    access_type = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = [
            "public_id",
            "name",
            "pan",
            "source_company",
            "info_received_date",
            "created_by",
            "created_at",
            "access_type",
            "status"
        ]

    def get_access_type(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None
        user = request.user
        
        if user.role in ['ADMIN', 'COMPLIANCE_OFFICER']:
            return 'EDIT' # Admins and Compliance Officers have full access
            
        if user.role == 'VIEWER':
            return 'VIEW' # Viewers always have View Only access

        # Use prefetched user_access to avoid N+1 queries
        try:
            for a in obj.user_access.all():
                if a.user_id == user.id:
                    return a.access_type
            return None
        except AttributeError:
            from .models import RecordAccess
            access = RecordAccess.objects.filter(record=obj, user=user).first()
            return access.access_type if access else None

# -------------------------------
# Detail Record Serializer
# -------------------------------
class RecordDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)
    updated_by_name = serializers.CharField(source="updated_by.name", read_only=True, allow_null=True)
    access_type = serializers.SerializerMethodField()
    access_list = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = [
            "public_id", "name", "designation", "employee_code", "pan",
            "source_company", "info_details", "info_received_date",
            "disclosure_name", "disclosure_designation", "disclosure_department",
            "created_by_name", "updated_by_name", "created_at", "updated_at",
            "access_type", "access_list"
        ]

    def get_access_type(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated: return None
        user = request.user
        if user.role in ['ADMIN', 'COMPLIANCE_OFFICER']: return 'EDIT'
        if user.role == 'VIEWER': return 'VIEW'
        # Use prefetched user_access to avoid N+1 queries
        try:
            for a in obj.user_access.all():
                if a.user_id == user.id:
                    return a.access_type
            return None
        except AttributeError:
            from .models import RecordAccess
            access = RecordAccess.objects.filter(record=obj, user=user).first()
            return access.access_type if access else None

    def get_access_list(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return []
        if request.user.role not in ['ADMIN', 'COMPLIANCE_OFFICER']:
            return []
        # Use prefetched user_access data to avoid N+1 queries
        try:
            accesses = obj.user_access.all()
        except AttributeError:
            from .models import RecordAccess
            accesses = RecordAccess.objects.filter(record=obj).select_related('user')
        return [
            {
                "user_id": a.user.public_id,
                "user_name": a.user.name,
                "user_email": a.user.email,
                "user_role": a.user.role,
                "access_type": a.access_type
            }
            for a in accesses
        ]