from rest_framework import serializers

from .models import Pin, PinRequest


class PinSerializer(serializers.ModelSerializer):
    purchasedAt = serializers.DateTimeField(source="created_at", format="%Y-%m-%d")
    token = serializers.CharField(source="code")
    status = serializers.SerializerMethodField()
    usedBy = serializers.SerializerMethodField()
    requestId = serializers.IntegerField(source="source_request_id", read_only=True)

    class Meta:
        model = Pin
        fields = ["id", "token", "status", "purchasedAt", "amount", "usedBy", "requestId"]

    def get_status(self, obj):
        return "available" if obj.status == "unused" else "used"

    def get_usedBy(self, obj):
        return obj.used_by.email if obj.used_by else ""


class PinRequestSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user.id", read_only=True)
    userName = serializers.SerializerMethodField()
    accountNumber = serializers.CharField(source="account_number")
    trxId = serializers.CharField(source="trx_id")
    requestedAt = serializers.DateTimeField(source="created_at", format="%Y-%m-%d")
    processedAt = serializers.DateTimeField(source="processed_at", format="%Y-%m-%d", allow_null=True)
    generatedPins = serializers.SerializerMethodField()
    adminNote = serializers.CharField(source="admin_note", read_only=True)

    class Meta:
        model = PinRequest
        fields = [
            "id",
            "userId",
            "userName",
            "accountNumber",
            "trxId",
            "amount",
            "status",
            "requestedAt",
            "processedAt",
            "quantity",
            "description",
            "adminNote",
            "generatedPins",
        ]

    def get_userName(self, obj):
        return obj.user.full_name

    def get_generatedPins(self, obj):
        return list(obj.generated_pins.values_list("code", flat=True))


class PinRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PinRequest
        fields = ["account_number", "trx_id", "quantity", "amount", "description"]
