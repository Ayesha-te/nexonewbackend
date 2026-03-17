from django.core.management.base import BaseCommand
from django.db.models import Sum

from accounts.models import User
from withdrawals.services import sync_user_pending_withdrawal
from wallets.models import LedgerEntry
from wallets.services import ensure_wallet


class Command(BaseCommand):
    help = "Reverse legacy pair_income credits and resync affected user balances."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the correction. Without this flag the command only shows a dry run.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        fixed_users = 0

        for user in User.objects.filter(is_staff=False).iterator():
            wallet = ensure_wallet(user)
            invalid_total = (
                LedgerEntry.objects.filter(wallet=wallet, entry_type="pair_income").aggregate(
                    total=Sum("amount")
                )["total"]
                or 0
            )
            reversal_total = (
                LedgerEntry.objects.filter(wallet=wallet, entry_type="pair_income_reversal").aggregate(
                    total=Sum("amount")
                )["total"]
                or 0
            )
            pending_reversal = invalid_total + reversal_total
            if pending_reversal <= 0:
                continue

            fixed_users += 1
            self.stdout.write(
                f"user={user.id} email={user.email} invalid_pair_income={pending_reversal}"
            )

            if not apply_changes:
                continue

            LedgerEntry.objects.create(
                wallet=wallet,
                amount=-pending_reversal,
                entry_type="pair_income_reversal",
                description="Reversal of legacy binary pair income",
                taxable_type="normal",
            )

            corrected_balance = (
                LedgerEntry.objects.filter(wallet=wallet).aggregate(total=Sum("amount"))["total"] or 0
            )
            corrected_balance = max(0, corrected_balance)

            wallet.balance = corrected_balance
            wallet.save(update_fields=["balance"])

            user.current_income = corrected_balance
            user.save(update_fields=["current_income"])

            sync_user_pending_withdrawal(user)

        mode = "Applied" if apply_changes else "Dry run"
        self.stdout.write(f"{mode} correction for {fixed_users} user(s).")
