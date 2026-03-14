from datetime import date

from django.contrib.auth import get_user_model
from django.db import transaction

from wallets.services import debit_wallet, ensure_wallet

from .models import AutoWithdrawalLog, Withdrawal

User = get_user_model()


def get_withdrawable_balance(user):
    wallet = ensure_wallet(user)
    balance = max(wallet.balance, user.current_income)
    if wallet.balance != balance:
        wallet.balance = balance
        wallet.save(update_fields=["balance"])
    return balance, wallet


def calculate_withdrawal_amounts(balance):
    amount = min(balance, 4000)
    tax_type = "normal"
    tax_rate = 0.05
    if amount >= 4000:
        tax_type = "cap"
        tax_rate = 0.10
    tax = int(round(amount * tax_rate))
    return {
        "amount": amount,
        "tax": tax,
        "tax_type": tax_type,
        "net_amount": amount - tax,
    }


def sync_user_pending_withdrawal(user, run_date=None):
    run_date = run_date or date.today()
    balance, _wallet = get_withdrawable_balance(user)
    pending = (
        Withdrawal.objects.filter(user=user, status="pending", auto_generated=True)
        .order_by("-date", "-id")
        .first()
    )

    if balance <= 0:
        if pending:
            pending.delete()
        return None

    amounts = calculate_withdrawal_amounts(balance)
    payload = {
        "payment_method": user.payment_method,
        "account_number": user.account_number,
        **amounts,
    }
    if pending:
        for field, value in payload.items():
            setattr(pending, field, value)
        pending.save(update_fields=list(payload.keys()))
        return pending
    return Withdrawal.objects.create(
        user=user,
        status="pending",
        auto_generated=True,
        date=run_date,
        **payload,
    )


def sync_all_pending_withdrawals(run_date=None):
    run_date = run_date or date.today()
    for user in User.objects.filter(is_staff=False, is_active=True):
        sync_user_pending_withdrawal(user, run_date=run_date)


@transaction.atomic
def approve_withdrawal(withdrawal):
    withdrawal = Withdrawal.objects.select_for_update().select_related("user").get(pk=withdrawal.pk)
    if withdrawal.status != "pending":
        raise ValueError("Withdrawal is already processed.")

    balance, _wallet = get_withdrawable_balance(withdrawal.user)
    if balance < withdrawal.amount:
        raise ValueError("User does not have enough balance for this withdrawal anymore.")

    debit_wallet(
        withdrawal.user,
        withdrawal.amount,
        "withdrawal",
        description=f"Withdrawal approved #{withdrawal.id}",
        taxable_type=withdrawal.tax_type,
    )
    withdrawal.status = "processed"
    withdrawal.save(update_fields=["status"])

    sync_user_pending_withdrawal(withdrawal.user)
    return withdrawal


def process_daily_auto_withdrawals(run_date=None):
    run_date = run_date or date.today()
    if AutoWithdrawalLog.objects.filter(run_date=run_date).exists():
        return 0
    processed = 0
    for user in User.objects.filter(is_staff=False, is_active=True):
        if sync_user_pending_withdrawal(user, run_date=run_date):
            processed += 1
    AutoWithdrawalLog.objects.create(run_date=run_date)
    return processed
