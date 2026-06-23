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
        ]

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
            "access_type"
        ]

    def get_access_type(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return None
        
        if user.role == 'ADMIN':
            return 'EDIT' # Admins have full access
            
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

    class Meta:
        model = Record
        fields = [
            "public_id", "name", "designation", "employee_code", "pan",
            "source_company", "info_details", "info_received_date",
            "disclosure_name", "disclosure_designation",
            "created_by_name", "updated_by_name", "created_at", "updated_at",
            "access_type"
        ]

    def get_access_type(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated: return None
        if user.role == 'ADMIN': return 'EDIT'
        from .models import RecordAccess
        access = RecordAccess.objects.filter(record=obj, user=user).first()
        return access.access_type if access else None