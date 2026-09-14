from rest_framework import serializers

from .models import AdsSettings, AdVideo, AdWatch


class AdWatchSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user_id")
    watchedDate = serializers.DateField(source="watched_date")
    rewardPkr = serializers.IntegerField(source="reward_pkr")
    cycleType = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    startedAt = serializers.DateTimeField(source="started_at")
    completedAt = serializers.DateTimeField(source="completed_at")
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = AdWatch
        fields = [
            "id",
            "userId",
            "watchedDate",
            "rewardPkr",
            "cycleType",
            "status",
            "startedAt",
            "completedAt",
            "createdAt",
        ]

    def get_cycleType(self, obj):
        return obj.cycle.cycle_type if obj.cycle else None


class AdVideoSerializer(serializers.ModelSerializer):
    videoUrl = serializers.SerializerMethodField()
    durationSeconds = serializers.IntegerField(source="duration_seconds", min_value=15, max_value=60)
    isActive = serializers.BooleanField(source="is_active")
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = AdVideo
        fields = [
            "id",
            "title",
            "video",
            "videoUrl",
            "durationSeconds",
            "isActive",
            "createdAt",
        ]
        extra_kwargs = {"video": {"write_only": True, "required": False}}

    def get_videoUrl(self, obj):
        if not obj.video:
            return None
        try:
            return obj.video.url
        except ValueError:
            return None


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
