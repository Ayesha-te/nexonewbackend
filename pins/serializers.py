from rest_framework import serializers

from .models import Pin, PinRequest


class PinSerializer(serializers.ModelSerializer):
    purchasedAt = serializers.DateTimeField(source="created_at", format="%Y-%m-%d")
    token = serializers.CharField(source="code")

    class Meta:
        model = Pin
        fields = ["id", "token", "status", "purchasedAt", "amount", "used_by"]


class PinRequestSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user.id", read_only=True)
    userName = serializers.SerializerMethodField()
    accountNumber = serializers.CharField(source="account_number")
    trxId = serializers.CharField(source="trx_id")
    requestedAt = serializers.DateTimeField(source="created_at", format="%Y-%m-%d")

    class Meta:
        model = PinRequest
        fields = ["id", "userId", "userName", "accountNumber", "trxId", "amount", "status", "requestedAt", "quantity", "description"]

    def get_userName(self, obj):
        return obj.user.full_name


class PinRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PinRequest
        fields = ["account_number", "trx_id", "quantity", "amount", "description"]
