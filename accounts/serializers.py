from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import PinActivationRequest, SignupLead

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    available_pins = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "account_number",
            "payment_method",
            "name",
            "first_name",
            "last_name",
            "profile_picture",
            "current_income",
            "reward_income",
            "total_withdrawn",
            "available_pins",
            "left_team_count",
            "right_team_count",
            "referral_code",
            "is_staff",
            "is_approved",
            "stop_earnings",
        ]
        read_only_fields = [
            "email",
            "phone",
            "account_number",
            "payment_method",
            "current_income",
            "reward_income",
            "total_withdrawn",
            "available_pins",
            "left_team_count",
            "right_team_count",
            "referral_code",
            "is_staff",
            "is_approved",
            "stop_earnings",
        ]

    def get_name(self, obj):
        return obj.full_name

    def get_available_pins(self, obj):
        return obj.pins.filter(status="unused").count()


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "profile_picture"]


class SignupLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignupLead
        fields = ["username", "email", "account_number", "referral_email"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists() or SignupLead.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value


class PinActivationSerializer(serializers.Serializer):
    pinToken = serializers.CharField()
    firstName = serializers.CharField()
    lastName = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    accountNumber = serializers.CharField()
    referralEmail = serializers.EmailField()
    position = serializers.ChoiceField(choices=["left", "right"])
    paymentMethod = serializers.ChoiceField(choices=["easypaisa", "jazzcash"])


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField()
    newPassword = serializers.CharField(min_length=6)


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "phone", "is_active", "stop_earnings"]


class AdminUserListSerializer(serializers.ModelSerializer):
    leftTeam = serializers.IntegerField(source="left_team_count")
    rightTeam = serializers.IntegerField(source="right_team_count")
    isActive = serializers.BooleanField(source="is_active")
    currentIncome = serializers.IntegerField(source="current_income")
    rewardIncome = serializers.IntegerField(source="reward_income")
    totalWithdraw = serializers.IntegerField(source="total_withdrawn")
    profilePic = serializers.SerializerMethodField()
    referralEmail = serializers.SerializerMethodField()
    position = serializers.CharField(source="placement_side")
    paymentMethod = serializers.CharField(source="payment_method")
    firstName = serializers.CharField(source="first_name")
    lastName = serializers.CharField(source="last_name")

    class Meta:
        model = User
        fields = [
            "id",
            "firstName",
            "lastName",
            "email",
            "phone",
            "profilePic",
            "referralEmail",
            "position",
            "paymentMethod",
            "isActive",
            "leftTeam",
            "rightTeam",
            "currentIncome",
            "rewardIncome",
            "totalWithdraw",
            "username",
        ]

    def get_profilePic(self, obj):
        if not obj.profile_picture:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(obj.profile_picture.url) if request else obj.profile_picture.url

    def get_referralEmail(self, obj):
        return obj.referred_by.email if obj.referred_by else ""
