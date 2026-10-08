from datetime import date

from django.contrib.auth import get_user_model

from wallets.services import credit_wallet

from .models import RewardTier, SalaryLog, UserReward

User = get_user_model()

REWARD_ROWS = [
    (1, 20, 20, "Experience Certificate", 0),
    (2, 50, 50, "1000 PKR", 1000),
    (3, 100, 100, "2000 PKR", 2000),
    (4, 200, 200, "5000 PKR", 5000),
    (5, 500, 500, "7000 PKR", 7000),
    (6, 1000, 1000, "10000 PKR", 10000),
    (7, 2000, 2000, "20000 PKR", 20000),
    (8, 5000, 5000, "35000 PKR", 35000),
    (9, 7500, 7500, "50000 PKR", 50000),
    (10, 10000, 10000, "70000 PKR", 70000),
    (11, 12500, 12500, "120000 PKR", 120000),
    (12, 20000, 20000, "230000 PKR", 230000),
    (13, 30000, 30000, "400000 PKR", 400000),
    (14, 40000, 40000, "750000 PKR", 750000),
    (15, 50000, 50000, "1200000 PKR", 1200000),
]


def seed_reward_tiers():
    if RewardTier.objects.exists():
        return

    for sequence, left_target, right_target, reward, amount in REWARD_ROWS:
        RewardTier.objects.get_or_create(
            sequence=sequence,
            defaults={
                "left_target": left_target,
                "right_target": right_target,
                "reward": reward,
                "amount": amount,
            },
        )


def award_matching_rewards(user):
    for tier in RewardTier.objects.all().order_by("sequence"):
        if user.left_team_count >= tier.left_target and user.right_team_count >= tier.right_target:
            reward_obj, created = UserReward.objects.get_or_create(user=user, tier=tier)
            if created and tier.amount > 0:
                credit_wallet(
                    user,
                    tier.amount,
                    "reward_income",
                    description=f"Reward unlocked: {tier.reward}",
                    taxable_type="reward",
                )


def process_monthly_salary(run_date=None):
    run_date = run_date or date.today()
    month_key = run_date.strftime("%Y-%m")
    processed = 0
    for user in User.objects.filter(pair_count__gte=50000, is_staff=False, is_active=True, is_approved=True):
        if SalaryLog.objects.filter(user=user, month=month_key).exists():
            continue
        user.stop_earnings = True
        user.save()
        SalaryLog.objects.create(user=user, month=month_key, amount=50000)
        credit_wallet(
            user,
            50000,
            "salary",
            description=f"Monthly salary for {month_key}",
            taxable_type="normal",
        )
        processed += 1
    return processed
