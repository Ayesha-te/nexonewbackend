from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Zeroes out financial records/aggregates (pins, pin requests, withdrawals, "
        "rewards, ads-earning history, wallet balances, ledger entries) for EVERY "
        "account, including staff/admin accounts - without deleting any user login. "
        "Use this after reset_platform if the admin panel's Financial Reports still "
        "show non-zero numbers left over from an admin/staff test account (reset_platform "
        "only deletes non-staff users, by design, so staff-owned test data survives it). "
        "This does NOT touch team/referral tree structure (left/right team counts, pair "
        "counts) or user accounts themselves. Irreversible - pass --yes to actually run it; "
        "otherwise it only reports what would be deleted/reset."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Actually perform the reset. Without this flag, only a dry-run count is printed.",
        )

    def handle(self, *args, **options):
        from pins.models import Pin, PinRequest
        from withdrawals.models import AutoWithdrawalLog, Withdrawal
        from rewards.models import SalaryLog, UserReward
        from ads.models import AdsCycle, AdWatch
        from wallets.models import LedgerEntry, Wallet

        counts = {
            "Pins": Pin.objects.count(),
            "PinRequests": PinRequest.objects.count(),
            "Withdrawals": Withdrawal.objects.count(),
            "AutoWithdrawalLogs": AutoWithdrawalLog.objects.count(),
            "UserRewards": UserReward.objects.count(),
            "SalaryLogs": SalaryLog.objects.count(),
            "AdWatches": AdWatch.objects.count(),
            "AdsCycles": AdsCycle.objects.count(),
            "LedgerEntries": LedgerEntry.objects.count(),
            "Wallets (to be zeroed, not deleted)": Wallet.objects.count(),
            "Users (income fields to be zeroed, not deleted)": User.objects.count(),
        }

        if not options["yes"]:
            self.stdout.write(self.style.WARNING("Dry run - nothing has been changed. Would affect:"))
            for label, count in counts.items():
                self.stdout.write(f"  {label}: {count}")
            self.stdout.write(self.style.WARNING("Re-run with --yes to actually perform this reset."))
            return

        with transaction.atomic():
            Pin.objects.all().delete()
            PinRequest.objects.all().delete()
            Withdrawal.objects.all().delete()
            AutoWithdrawalLog.objects.all().delete()
            UserReward.objects.all().delete()
            SalaryLog.objects.all().delete()
            AdWatch.objects.all().delete()
            AdsCycle.objects.all().delete()
            LedgerEntry.objects.all().delete()
            Wallet.objects.update(balance=0, income_pkr=0, reward_balance=0, hold_pkr=0)
            User.objects.update(current_income=0, reward_income=0, total_withdrawn=0)

        self.stdout.write(self.style.SUCCESS("All financial records have been reset to zero."))
