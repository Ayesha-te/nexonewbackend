from rest_framework import serializers

from .models import AdsSettings, AdWatch


class AdWatchSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_id")
    watchedDate = serializers.DateField(source="watched_date")
    rewardPkr = serializers.IntegerField(source="reward_pkr")
    cycleType = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = AdWatch
        fields = [
            "id",
            "userId",
            "watchedDate",
            "rewardPkr",
            "cycleType",
            "createdAt",
        ]

    def get_cycleType(self, obj):
        return obj.cycle.cycle_type if obj.cycle else None


class AdsSettingsSerializer(serializers.ModelSerializer):
    enabled = serializers.BooleanField()
    dailyLimit = serializers.IntegerField(source="daily_limit")
    welcomeRewardPkr = serializers.IntegerField(source="welcome_reward_pkr")
    welcomeDurationDays = serializers.IntegerField(source="welcome_duration_days")
    pairRewardPkr = serializers.IntegerField(source="pair_reward_pkr")
    pairCycleDays = serializers.IntegerField(source="pair_cycle_days")
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = AdsSettings
        fields = [
            "id",
            "enabled",
            "dailyLimit",
            "welcomeRewardPkr",
            "welcomeDurationDays",
            "pairRewardPkr",
            "pairCycleDays",
            "updatedAt",
        ]
