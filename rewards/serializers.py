from rest_framework import serializers

from .models import RewardTier, UserReward


class RewardTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardTier
        fields = ["sequence", "left_target", "right_target", "reward", "amount"]


class UserRewardSerializer(serializers.ModelSerializer):
    reward = serializers.CharField(source="tier.reward")
    amount = serializers.IntegerField(source="tier.amount")

    class Meta:
        model = UserReward
        fields = ["id", "reward", "amount", "rewarded_at"]
