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
    if not normalized_sponsor_email:
        raise ValueError("Referral email not found.")
    sponsor = User.objects.filter(email__iexact=normalized_sponsor_email).first()
    if not sponsor:
        raise ValueError("Referral email not found.")
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
        current.pair_count = min(current.left_team_count, current.right_team_count)
        current.save(update_fields=["left_team_count", "right_team_count", "pair_count"])
        award_matching_rewards(current)
        award_binary_set_income(current)
        side_value = current.placement_side
        current = current.placement_parent


def award_binary_set_income(user):
    if user.stop_earnings:
        return

    completed_sets = user.pair_count
    newly_completed_sets = max(completed_sets - user.auto_pair_income_pairs, 0)
    if newly_completed_sets <= 0:
        return

    starting_set_number = user.auto_pair_income_pairs
    for offset in range(newly_completed_sets):
        set_number = starting_set_number + offset + 1
        if set_number == 1:
            amount = 400
        elif set_number <= 99:
            amount = 200
        else:
            amount = 100
        credit_wallet(
            user,
            amount,
            "binary_set_income",
            description=f"Binary set income #{set_number}",
            taxable_type="normal",
        )
    user.auto_pair_income_pairs += newly_completed_sets
    user.save(update_fields=["auto_pair_income_pairs"])


def collect_subtree_user_ids(root_user_id):
    subtree_ids = {root_user_id}
    frontier = [root_user_id]

    while frontier:
        child_ids = list(
            BinaryNode.objects.filter(parent_id__in=frontier).values_list("user_id", flat=True)
        )
        child_ids = [child_id for child_id in child_ids if child_id not in subtree_ids]
        subtree_ids.update(child_ids)
        frontier = child_ids

    return subtree_ids


def rebuild_network_metrics():
    users = {
        user.id: user
        for user in User.objects.filter(is_staff=False)
    }
    children_by_parent = {}

    for node in BinaryNode.objects.filter(user_id__in=users.keys()).values("user_id", "parent_id", "side"):
        parent_id = node["parent_id"]
        if parent_id not in users:
            continue
        children_by_parent.setdefault(parent_id, {})[node["side"]] = node["user_id"]

    def compute_counts(user_id):
        children = children_by_parent.get(user_id, {})
        left_user_id = children.get("left")
        right_user_id = children.get("right")

        left_count = 0 if left_user_id is None else 1 + compute_counts(left_user_id)
        right_count = 0 if right_user_id is None else 1 + compute_counts(right_user_id)

        user = users[user_id]
        user.left_team_count = left_count
        user.right_team_count = right_count
        user.pair_count = min(left_count, right_count)

        return left_count + right_count

    for user_id in users:
        compute_counts(user_id)

    User.objects.bulk_update(
        users.values(),
        ["left_team_count", "right_team_count", "pair_count"],
    )


@transaction.atomic
def delete_user_subtree(*, user):
    if user.is_staff:
        raise ValueError("Admin users cannot be deleted from this screen.")

    subtree_ids = collect_subtree_user_ids(user.id)
    deleted_count = len(subtree_ids)
    User.objects.filter(id__in=subtree_ids, is_staff=False).delete()
    rebuild_network_metrics()
    return deleted_count
