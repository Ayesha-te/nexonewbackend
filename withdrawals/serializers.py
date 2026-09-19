from rest_framework import serializers

from .models import Withdrawal


class WithdrawalSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user.id", read_only=True)
    userName = serializers.SerializerMethodField()
    userEmail = serializers.EmailField(source="user.email", read_only=True)
    paymentMethod = serializers.CharField(source="payment_method")
    bankName = serializers.CharField(source="bank_name")
    accountNumber = serializers.CharField(source="account_number")
    taxType = serializers.CharField(source="tax_type")
    netAmount = serializers.IntegerField(source="net_amount")
    leftTeamTotal = serializers.IntegerField(source="left_team_total")
    rightTeamTotal = serializers.IntegerField(source="right_team_total")
    totalTeam = serializers.SerializerMethodField()
    unmatchedTeam = serializers.SerializerMethodField()
    matchedPairs = serializers.IntegerField(source="matched_pairs")
    systemAddedEarnings = serializers.IntegerField(source="system_added_earnings")
    adsEarningTotal = serializers.SerializerMethodField()
    requestedAmount = serializers.IntegerField(source="amount")
    adminAdjustment = serializers.IntegerField(source="admin_adjustment")
    adminNote = serializers.CharField(source="admin_note")
    finalAmount = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at")
    processedAt = serializers.DateTimeField(source="processed_at")

    class Meta:
        model = Withdrawal
        fields = [
            "id",
            "userId",
            "userName",
            "userEmail",
            "paymentMethod",
            "bankName",
            "accountNumber",
            "amount",
            "requestedAmount",
            "tax",
            "taxType",
            "netAmount",
            "leftTeamTotal",
            "rightTeamTotal",
            "totalTeam",
            "unmatchedTeam",
            "matchedPairs",
            "systemAddedEarnings",
            "adsEarningTotal",
            "adminAdjustment",
            "adminNote",
            "finalAmount",
            "date",
            "status",
            "createdAt",
            "processedAt",
        ]

    def get_userName(self, obj):
        return obj.user.full_name

    def get_totalTeam(self, obj):
        return obj.left_team_total + obj.right_team_total

    def get_unmatchedTeam(self, obj):
        return abs(obj.left_team_total - obj.right_team_total)

    def get_adsEarningTotal(self, obj):
        # Batch-computed by the view (one aggregate query for the whole list) and passed
        # in via context, so rendering N withdrawals never issues N extra queries.
        return self.context.get("ads_totals_by_user_id", {}).get(obj.user_id, 0)

    def get_finalAmount(self, obj):
        return max(obj.amount + obj.admin_adjustment, 0)
