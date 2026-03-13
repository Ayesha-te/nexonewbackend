from rest_framework import serializers

from .models import Withdrawal


class WithdrawalSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user.id", read_only=True)
    userName = serializers.SerializerMethodField()
    paymentMethod = serializers.CharField(source="payment_method")
    accountNumber = serializers.CharField(source="account_number")
    taxType = serializers.CharField(source="tax_type")
    netAmount = serializers.IntegerField(source="net_amount")

    class Meta:
        model = Withdrawal
        fields = [
            "id",
            "userId",
            "userName",
            "paymentMethod",
            "accountNumber",
            "amount",
            "tax",
            "taxType",
            "netAmount",
            "date",
            "status",
        ]

    def get_userName(self, obj):
        return obj.user.full_name
