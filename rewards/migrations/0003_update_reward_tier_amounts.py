from django.db import migrations

# Matches rewards.services.REWARD_ROWS after the final approved reward structure update.
# Left/right targets (sequence stays the stable key) are unchanged - only the reward label
# and cash amount change. This only updates the RewardTier rows (future unlock amounts);
# it does NOT touch any existing UserReward row or any wallet/ledger transaction already
# recorded for a reward a user already unlocked - those already happened at the old rate
# and stay exactly as they are.
NEW_AMOUNTS = {
    1: ("Experience Certificate", 0),
    2: ("1000 PKR", 1000),
    3: ("2000 PKR", 2000),
    4: ("5000 PKR", 5000),
    5: ("7000 PKR", 7000),
    6: ("10000 PKR", 10000),
    7: ("20000 PKR", 20000),
    8: ("35000 PKR", 35000),
    9: ("50000 PKR", 50000),
    10: ("70000 PKR", 70000),
    11: ("120000 PKR", 120000),
    12: ("230000 PKR", 230000),
    13: ("400000 PKR", 400000),
    14: ("750000 PKR", 750000),
    15: ("1200000 PKR", 1200000),
}


def update_amounts(apps, schema_editor):
    RewardTier = apps.get_model("rewards", "RewardTier")
    for sequence, (reward, amount) in NEW_AMOUNTS.items():
        RewardTier.objects.filter(sequence=sequence).update(reward=reward, amount=amount)


def revert_amounts(apps, schema_editor):
    RewardTier = apps.get_model("rewards", "RewardTier")
    old_amounts = {
        1: ("Experience Certificate", 0),
        2: ("Perfume Gift", 0),
        3: ("3000 PKR", 3000),
        4: ("5000 PKR", 5000),
        5: ("7000 PKR", 7000),
        6: ("10000 PKR", 10000),
        7: ("25000 PKR", 25000),
        8: ("50000 PKR", 50000),
        9: ("80000 PKR", 80000),
        10: ("120000 PKR", 120000),
        11: ("200000 PKR", 200000),
        12: ("400000 PKR", 400000),
        13: ("600000 PKR", 600000),
        14: ("900000 PKR", 900000),
        15: ("1500000 PKR", 1500000),
    }
    for sequence, (reward, amount) in old_amounts.items():
        RewardTier.objects.filter(sequence=sequence).update(reward=reward, amount=amount)


class Migration(migrations.Migration):

    dependencies = [
        ("rewards", "0002_alter_rewardtier_sequence"),
    ]

    operations = [
        migrations.RunPython(update_amounts, reverse_code=revert_amounts),
    ]
