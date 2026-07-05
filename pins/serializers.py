from rest_framework import serializers

from .models import MAX_PIN_PURCHASE_QUANTITY, MIN_PIN_PURCHASE_QUANTITY, PIN_PRICE, Pin, PinPurchaseSettings, PinRequest


class PinSerializer(serializers.ModelSerializer):
    purchasedAt = serializers.DateTimeField(source="created_at", format="%Y-%m-%d")
    token = serializers.CharField(source="code")
    status = serializers.SerializerMethodField()
    usedBy = serializers.SerializerMethodField()
    requestId = serializers.IntegerField(source="source_request_id", read_only=True)

    class Meta:
        model = Pin
        fields = ["id", "token", "status", "purchasedAt", "amount", "usedBy", "requestId"]

    def get_status(self, obj):
        return "available" if obj.status == "unused" else "used"

    def get_usedBy(self, obj):
        return obj.used_by.email if obj.used_by else ""


class PinRequestSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source="user.id", read_only=True)
    userName = serializers.SerializerMethodField()
    accountNumber = serializers.CharField(source="account_number")
    trxId = serializers.CharField(source="trx_id")
    requestedAt = serializers.DateTimeField(source="created_at", format="%Y-%m-%d %H:%M")
    processedAt = serializers.DateTimeField(source="processed_at", format="%Y-%m-%d %H:%M", allow_null=True)
    generatedPins = serializers.SerializerMethodField()
    adminNote = serializers.CharField(source="admin_note", read_only=True)
    screenshotUrl = serializers.SerializerMethodField()

    class Meta:
        model = PinRequest
        fields = [
            "id",
            "userId",
            "userName",
            "accountNumber",
            "trxId",
            "amount",
            "status",
            "requestedAt",
            "processedAt",
            "quantity",
            "description",
            "adminNote",
            "generatedPins",
            "screenshotUrl",
        ]

    def get_userName(self, obj):
        return obj.user.full_name

    def get_generatedPins(self, obj):
        return list(obj.generated_pins.values_list("code", flat=True))

    def get_screenshotUrl(self, obj):
        if not obj.payment_screenshot:
            return None
        request = self.context.get("request")
        url = obj.payment_screenshot.url
        return request.build_absolute_uri(url) if request else url


class PinRequestCreateSerializer(serializers.ModelSerializer):
    proofFile = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = PinRequest
        fields = ["account_number", "trx_id", "quantity", "amount", "description", "proofFile"]
        extra_kwargs = {
            "account_number": {"required": False, "allow_blank": True},
            "amount": {"required": False},
            "description": {"required": False, "allow_blank": True},
        }

    def validate_quantity(self, value):
        if value < MIN_PIN_PURCHASE_QUANTITY or value > MAX_PIN_PURCHASE_QUANTITY:
            raise serializers.ValidationError(
                f"PIN quantity must be between {MIN_PIN_PURCHASE_QUANTITY} and {MAX_PIN_PURCHASE_QUANTITY}."
            )
        return value

    def validate(self, attrs):
        attrs.pop("amount", None)
        attrs["amount"] = attrs["quantity"] * PIN_PRICE
        return attrs


class PinPurchaseSettingsSerializer(serializers.ModelSerializer):
    purchaseEnabled = serializers.BooleanField(source="purchase_enabled")
    disabledMessage = serializers.SerializerMethodField()
    pinPrice = serializers.SerializerMethodField()
    minQuantity = serializers.SerializerMethodField()
    maxQuantity = serializers.SerializerMethodField()
    paymentDetails = serializers.SerializerMethodField()

    class Meta:
        model = PinPurchaseSettings
        fields = ["purchaseEnabled", "disabledMessage", "pinPrice", "minQuantity", "maxQuantity", "paymentDetails"]

    def get_disabledMessage(self, obj):
        from .models import PIN_PURCHASE_DISABLED_MESSAGE

        return PIN_PURCHASE_DISABLED_MESSAGE

    def get_pinPrice(self, obj):
        return PIN_PRICE

    def get_minQuantity(self, obj):
        return MIN_PIN_PURCHASE_QUANTITY

    def get_maxQuantity(self, obj):
        return MAX_PIN_PURCHASE_QUANTITY

    def get_paymentDetails(self, obj):
        request = self.context.get("request")
        qr_url = obj.qr_code.url if obj.qr_code else None
        return {
            "accountTitle": obj.account_title,
            "accountNumber": obj.account_number,
            "paymentMethod": obj.payment_method,
            "instructions": obj.instructions,
            "qrCodeUrl": request.build_absolute_uri(qr_url) if request and qr_url else qr_url,
        }


class PinPurchaseSettingsUpdateSerializer(serializers.ModelSerializer):
    purchaseEnabled = serializers.BooleanField(source="purchase_enabled")
    accountTitle = serializers.CharField(source="account_title", max_length=128)
    accountNumber = serializers.CharField(source="account_number", max_length=64)
    paymentMethod = serializers.ChoiceField(source="payment_method", choices=PinPurchaseSettings.PAYMENT_METHOD_CHOICES)
    qrCode = serializers.FileField(source="qr_code", required=False, allow_null=True)

    class Meta:
        model = PinPurchaseSettings
        fields = ["purchaseEnabled", "accountTitle", "accountNumber", "paymentMethod", "instructions", "qrCode"]
