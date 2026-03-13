from django.contrib.auth import get_user_model
from django.db import transaction

from network.models import BinaryNode
from pins.models import Pin
from rewards.services import award_matching_rewards
from wallets.services import credit_wallet, ensure_wallet

User = get_user_model()


def create_user_from_pin(*, sponsor_email, pin_code, first_name, last_name, email, phone, account_number, position, payment_method):
    sponsor = User.objects.filter(email__iexact=sponsor_email).first()
    if not sponsor:
        raise ValueError("Referral email not found.")
    pin = Pin.objects.filter(code=pin_code, owner=sponsor, status="unused").first()
    if not pin:
        raise ValueError("Pin is invalid or already used.")
    if User.objects.filter(email__iexact=email).exists():
        raise ValueError("User email already exists.")
    username_base = email.split("@")[0]
    username = username_base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{username_base}{suffix}"
    with transaction.atomic():
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=phone,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            account_number=account_number,
            payment_method=payment_method,
            referred_by=sponsor,
            placement_parent=sponsor,
            placement_side=position,
            is_approved=True,
            is_active=True,
        )
        ensure_wallet(new_user)
        pin.status = "used"
        pin.used_by = new_user
        pin.save()
        BinaryNode.objects.create(user=new_user, parent=sponsor, side=position)
        cascade_team_updates(sponsor, position)
    return new_user


def cascade_team_updates(user, side):
    current = user
    side_value = side
    while current:
        if side_value == "left":
            current.left_team_count += 1
        else:
            current.right_team_count += 1
        new_pairs = min(current.left_team_count, current.right_team_count) - current.pair_count
        if new_pairs > 0 and not current.stop_earnings and current.pair_count < 50000:
            for pair_number in range(current.pair_count + 1, current.pair_count + new_pairs + 1):
                amount = 400 if pair_number == 1 else 200
                credit_wallet(
                    current,
                    amount,
                    "pair_income",
                    description=f"Pair income #{pair_number}",
                    taxable_type="normal",
                )
            current.pair_count += new_pairs
        current.save()
        award_matching_rewards(current)
        side_value = current.placement_side
        current = current.placement_parent
