from django.contrib.auth import get_user_model
from django.db import transaction

from network.models import BinaryNode
from network.services import find_next_open_slot
from pins.models import Pin
from rewards.services import award_matching_rewards
from wallets.services import credit_wallet, ensure_wallet

User = get_user_model()


def create_user_from_pin(
    *,
    activating_user,
    sponsor_email,
    pin_code,
    first_name,
    last_name,
    email,
    phone,
    account_number,
    position,
    payment_method,
):
    normalized_sponsor_email = (sponsor_email or "").strip().lower()
    active_user_email = (activating_user.email or "").strip().lower()
    if not normalized_sponsor_email:
        raise ValueError("Referral email not found.")
    if normalized_sponsor_email != active_user_email:
        raise ValueError("Referral email must match your active account email.")
    sponsor = activating_user
    pin = Pin.objects.filter(code=pin_code, owner=activating_user, status="unused").first()
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
        placement_parent, placement_side = find_next_open_slot(sponsor, position)
        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            account_number=account_number,
            payment_method=payment_method,
            referred_by=sponsor,
            placement_parent=placement_parent,
            placement_side=placement_side,
            is_approved=True,
            is_active=True,
        )
        ensure_wallet(new_user)
        pin.status = "used"
        pin.used_by = new_user
        pin.save()
        BinaryNode.objects.create(user=new_user, parent=placement_parent, side=placement_side)
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
                amount = get_pair_reward_amount(pair_number)
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


def get_pair_reward_amount(pair_number):
    if pair_number == 1:
        return 400
    if pair_number <= 99:
        return 200
    return 100
