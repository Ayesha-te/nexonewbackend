from datetime import date

from django.contrib.auth import get_user_model

from wallets.services import debit_wallet, ensure_wallet

from .models import AutoWithdrawalLog, Withdrawal

User = get_user_model()


def process_daily_auto_withdrawals(run_date=None):
    run_date = run_date or date.today()
    if AutoWithdrawalLog.objects.filter(run_date=run_date).exists():
        return 0
    processed = 0
    for user in User.objects.filter(is_staff=False, is_active=True, is_approved=True):
        wallet = ensure_wallet(user)
        if wallet.balance <= 0:
            continue
        amount = min(wallet.balance, 4000)
        tax_type = "normal"
        tax_rate = 0.05
        if amount >= 4000:
            tax_type = "cap"
            tax_rate = 0.10
        tax = int(round(amount * tax_rate))
        net_amount = amount - tax
        Withdrawal.objects.create(
            user=user,
            payment_method=user.payment_method,
            account_number=user.account_number,
            amount=amount,
            tax=tax,
            tax_type=tax_type,
            net_amount=net_amount,
            date=run_date,
            status="processed",
            auto_generated=True,
        )
        debit_wallet(user, amount, "withdrawal", description=f"Auto withdrawal for {run_date}", taxable_type=tax_type)
        processed += 1
    AutoWithdrawalLog.objects.create(run_date=run_date)
    return processed
