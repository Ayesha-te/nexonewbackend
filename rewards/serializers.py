from rest_framework import serializers

from .models import RewardTier, UserReward


class RewardTierSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(source="sequence", read_only=True)
    left = serializers.IntegerField(source="left_target", read_only=True)
    right = serializers.IntegerField(source="right_target", read_only=True)

    class Meta:
        model = RewardTier
        fields = ["level", "left", "right", "reward", "amount"]


class UserRewardSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(source="tier.sequence", read_only=True)
    reward = serializers.CharField(source="tier.reward")
    rewardedAt = serializers.DateTimeField(source="rewarded_at", format="%Y-%m-%d")

    class Meta:
        model = UserReward
        # `amount` is the model's own frozen-at-credit-time field (not tier.amount), so a
        # later change to the tier's amount never retroactively changes what a user sees
        # for a reward they already earned.
        fields = ["id", "level", "reward", "amount", "rewardedAt"]


class AdminUserRewardSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user.id", read_only=True)
    userName = serializers.CharField(source="user.full_name", read_only=True)
    userEmail = serializers.CharField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    level = serializers.IntegerField(source="tier.sequence", read_only=True)
    milestone = serializers.CharField(source="tier.reward", read_only=True)
    rewardedAt = serializers.DateTimeField(source="rewarded_at", format="%Y-%m-%d %H:%M")
    referenceId = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = UserReward
        fields = [
            "id",
            "userId",
            "userName",
            "userEmail",
            "username",
            "level",
            "milestone",
            "amount",
            "rewardedAt",
            "referenceId",
            "status",
        ]

    def get_referenceId(self, obj):
        return f"LEDGER-{obj.ledger_entry_id}" if obj.ledger_entry_id else f"UR-{obj.id}"

    def get_status(self, obj):
        # Rewards in this system are awarded automatically and atomically alongside their
        # wallet credit - there is no pending/partial state, every existing row is final.
        return "Credited"
