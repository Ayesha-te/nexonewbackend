from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

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


def get_payment_label(payment_method):
    if payment_method == "easypaisa":
        return "EasyPaisa"
    if payment_method == "jazzcash":
        return "JazzCash"
    if payment_method == "bank_account":
        return "Bank Account"
    return payment_method or "Account"


def sync_user_pending_withdrawal(user, run_date=None):
    # No row locking here on purpose: this only recomputes a *preview* pending-withdrawal
    # row from the user's current balance and never moves money (only approve_withdrawal
    # does that, and it still holds a full user-row lock). Locking here was correct but too
    # slow once run for every active user on every admin page load (88+ users started
    # exceeding the platform's ~30s request timeout). The unique constraint on
    # (user, status="pending", auto_generated=True) still makes a genuine duplicate
    # impossible at the database level; a rare concurrent double-create just falls back to
    # reusing whichever row won, handled below.
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
        "bank_name": user.bank_name if user.payment_method == "bank_account" else get_payment_label(user.payment_method),
        "account_name": user.full_name or user.username or user.email,
        "account_number": user.account_number,
        "tx_id": "",
        "left_team_total": user.left_team_count,
        "right_team_total": user.right_team_count,
        "matched_pairs": user.pair_count,
        "system_added_earnings": user.system_pair_income_total,
        **amounts,
    }
    if pending:
        for field, value in payload.items():
            setattr(pending, field, value)
        pending.save(update_fields=list(payload.keys()))
        return pending

    try:
        with transaction.atomic():
            return Withdrawal.objects.create(
                user=user,
                status="pending",
                auto_generated=True,
                date=run_date,
                created_at=timezone.now(),
                **payload,
            )
    except IntegrityError:
        return (
            Withdrawal.objects.filter(user=user, status="pending", auto_generated=True)
            .order_by("-date", "-id")
            .first()
        )


def sync_all_pending_withdrawals(run_date=None):
    run_date = run_date or date.today()
    for user in User.objects.filter(is_staff=False, is_active=True):
        sync_user_pending_withdrawal(user, run_date=run_date)


@transaction.atomic
def approve_withdrawal(withdrawal, *, admin_adjustment=0, admin_note=""):
    # Lock the user row before the withdrawal row. If this user somehow has more than one
    # pending withdrawal, or a concurrent request is approving another one of theirs at the
    # same time, this forces those calls to run one after another instead of both reading
    # the same stale balance and both debiting it.
    user = User.objects.select_for_update().get(pk=withdrawal.user_id)
    withdrawal = Withdrawal.objects.select_for_update().get(pk=withdrawal.pk)
    if withdrawal.status != "pending":
        raise ValueError("Withdrawal is already processed.")

    balance, _wallet = get_withdrawable_balance(user)
    if balance < withdrawal.amount:
        raise ValueError("User does not have enough balance for this withdrawal anymore.")

    debit_wallet(
        user,
        withdrawal.amount,
        "withdrawal",
        description=f"Withdrawal approved #{withdrawal.id}",
        taxable_type=withdrawal.tax_type,
    )
    withdrawal.admin_adjustment = admin_adjustment
    withdrawal.admin_note = admin_note
    withdrawal.status = "processed"
    withdrawal.save(update_fields=["admin_adjustment", "admin_note", "status"])

    sync_user_pending_withdrawal(user)
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
