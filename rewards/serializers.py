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
    amount = serializers.IntegerField(source="tier.amount")
    rewardedAt = serializers.DateTimeField(source="rewarded_at", format="%Y-%m-%d")

    class Meta:
        model = UserReward
        fields = ["id", "level", "reward", "amount", "rewardedAt"]
