import base64

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import PinActivationRequest, SignupLead

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    available_pins = serializers.SerializerMethodField()
    referral_email = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    system_pair_income_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "account_number",
            "payment_method",
            "bank_name",
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
            "pair_count",
            "auto_pair_income_pairs",
            "system_pair_income_total",
            "referral_code",
            "referral_email",
            "is_staff",
            "is_active",
            "is_approved",
            "stop_earnings",
            "created_at",
        ]
        read_only_fields = [
            "email",
            "phone",
            "account_number",
            "payment_method",
            "bank_name",
            "current_income",
            "reward_income",
            "total_withdrawn",
            "available_pins",
            "left_team_count",
            "right_team_count",
            "pair_count",
            "auto_pair_income_pairs",
            "system_pair_income_total",
            "referral_code",
            "referral_email",
            "is_staff",
            "is_active",
            "is_approved",
            "stop_earnings",
            "created_at",
        ]

    def get_name(self, obj):
        return obj.full_name

    def get_available_pins(self, obj):
        return obj.pins.filter(status="unused").count()

    def get_referral_email(self, obj):
        return obj.referred_by.email if obj.referred_by else ""

    def get_profile_picture(self, obj):
        if obj.profile_picture_data_url:
            return obj.profile_picture_data_url
        if not obj.profile_picture:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(obj.profile_picture.url) if request else obj.profile_picture.url


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "profile_picture"]

    def update(self, instance, validated_data):
        uploaded_picture = validated_data.get("profile_picture")
        data_url = None

        if uploaded_picture:
            content = uploaded_picture.read()
            uploaded_picture.seek(0)
            content_type = getattr(uploaded_picture, "content_type", None) or "image/jpeg"
            encoded = base64.b64encode(content).decode("ascii")
            data_url = f"data:{content_type};base64,{encoded}"

        instance = super().update(instance, validated_data)

        if data_url is not None:
            instance.profile_picture_data_url = data_url
            instance.save(update_fields=["profile_picture_data_url"])

        return instance


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
    bankName = serializers.CharField(required=False, allow_blank=True)
    referralEmail = serializers.EmailField()
    position = serializers.ChoiceField(choices=["left", "right"])
    paymentMethod = serializers.ChoiceField(choices=["easypaisa", "jazzcash", "bank_account"])

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get("paymentMethod") == "bank_account" and not attrs.get("bankName", "").strip():
            raise serializers.ValidationError({"bankName": "Bank name is required when payment method is Bank Account."})
        if attrs.get("paymentMethod") != "bank_account":
            attrs["bankName"] = ""
        return attrs


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
    accountNumber = serializers.CharField(source="account_number")
    bankName = serializers.CharField(source="bank_name")
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
            "accountNumber",
            "bankName",
            "isActive",
            "leftTeam",
            "rightTeam",
            "currentIncome",
            "rewardIncome",
            "totalWithdraw",
            "username",
        ]

    def get_profilePic(self, obj):
        if obj.profile_picture_data_url:
            return obj.profile_picture_data_url
        if not obj.profile_picture:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(obj.profile_picture.url) if request else obj.profile_picture.url

    def get_referralEmail(self, obj):
        return obj.referred_by.email if obj.referred_by else ""


class LeaderboardUserSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="id")
    userName = serializers.CharField(source="full_name")
    profilePic = serializers.SerializerMethodField()
    currentIncome = serializers.IntegerField()
    weeklyIncome = serializers.IntegerField()
    monthlyIncome = serializers.IntegerField()
    totalIncome = serializers.IntegerField()

    class Meta:
        model = User
        fields = [
            "userId",
            "userName",
            "profilePic",
            "currentIncome",
            "weeklyIncome",
            "monthlyIncome",
            "totalIncome",
        ]

    def get_profilePic(self, obj):
        if obj.profile_picture_data_url:
            return obj.profile_picture_data_url
        if not obj.profile_picture:
            return ""
        request = self.context.get("request")
        return request.build_absolute_uri(obj.profile_picture.url) if request else obj.profile_picture.url
