from rest_framework import serializers

from .models import Withdrawal


class WithdrawalSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user.id", read_only=True)
    userName = serializers.SerializerMethodField()
    paymentMethod = serializers.CharField(source="payment_method")
    accountNumber = serializers.CharField(source="account_number")
    taxType = serializers.CharField(source="tax_type")
    netAmount = serializers.IntegerField(source="net_amount")
    leftTeamTotal = serializers.IntegerField(source="left_team_total")
    rightTeamTotal = serializers.IntegerField(source="right_team_total")
    matchedPairs = serializers.IntegerField(source="matched_pairs")
    systemAddedEarnings = serializers.IntegerField(source="system_added_earnings")
    requestedAmount = serializers.IntegerField(source="amount")
    adminAdjustment = serializers.IntegerField(source="admin_adjustment")
    adminNote = serializers.CharField(source="admin_note")
    finalAmount = serializers.SerializerMethodField()

    class Meta:
        model = Withdrawal
        fields = [
            "id",
            "userId",
            "userName",
            "paymentMethod",
            "accountNumber",
            "amount",
            "requestedAmount",
            "tax",
            "taxType",
            "netAmount",
            "leftTeamTotal",
            "rightTeamTotal",
            "matchedPairs",
            "systemAddedEarnings",
            "adminAdjustment",
            "adminNote",
            "finalAmount",
            "date",
            "status",
        ]

    def get_userName(self, obj):
        return obj.user.full_name

    def get_finalAmount(self, obj):
        return max(obj.amount + obj.admin_adjustment, 0)
