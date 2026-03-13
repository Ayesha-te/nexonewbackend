from rest_framework import serializers

from .models import LedgerEntry, Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["balance", "reward_balance"]


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ["id", "amount", "entry_type", "description", "taxable_type", "created_at"]
