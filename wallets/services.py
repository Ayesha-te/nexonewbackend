from .models import LedgerEntry, Wallet


def ensure_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def credit_wallet(user, amount, entry_type, description="", taxable_type="normal"):
    wallet = ensure_wallet(user)
    wallet.balance += amount
    if entry_type == "reward_income":
        wallet.reward_balance += amount
        user.reward_income += amount
    user.current_income += amount
    wallet.save()
    user.save()
    return LedgerEntry.objects.create(
        wallet=wallet,
        amount=amount,
        entry_type=entry_type,
        description=description,
        taxable_type=taxable_type,
    )


def debit_wallet(user, amount, entry_type, description="", taxable_type="normal"):
    wallet = ensure_wallet(user)
    wallet.balance = max(0, wallet.balance - amount)
    wallet.save()
    user.current_income = max(0, user.current_income - amount)
    user.total_withdrawn += amount
    user.save()
    return LedgerEntry.objects.create(
        wallet=wallet,
        amount=-amount,
        entry_type=entry_type,
        description=description,
        taxable_type=taxable_type,
    )
