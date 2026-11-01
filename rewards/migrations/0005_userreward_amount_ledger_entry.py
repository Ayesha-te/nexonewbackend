import django.db.models.deletion
from django.db import migrations, models


def backfill_amount_and_ledger_entry(apps, schema_editor):
    """
    Every UserReward row with a non-zero tier amount was created in the same call that
    credited exactly one wallets.LedgerEntry with entry_type="reward_income" for that same
    user (rewards.services.award_matching_rewards) - no other code path creates that entry
    type. So for each user, zipping their UserReward rows (ordered by rewarded_at) against
    their reward_income LedgerEntry rows (ordered by created_at) reconstructs the real
    historical pairing without inventing any data. Where the counts don't line up for some
    user (shouldn't normally happen), leave amount at today's tier amount as the best
    available fallback rather than guessing a mismatched pairing.
    """
    UserReward = apps.get_model("rewards", "UserReward")
    LedgerEntry = apps.get_model("wallets", "LedgerEntry")

    rewards_by_user = {}
    for reward in UserReward.objects.select_related("tier").order_by("user_id", "rewarded_at", "id"):
        rewards_by_user.setdefault(reward.user_id, []).append(reward)

    ledger_by_user = {}
    for entry in (
        LedgerEntry.objects.filter(entry_type="reward_income")
        .select_related("wallet")
        .order_by("wallet__user_id", "created_at", "id")
    ):
        ledger_by_user.setdefault(entry.wallet.user_id, []).append(entry)

    to_update = []
    for user_id, user_rewards in rewards_by_user.items():
        ledger_entries = ledger_by_user.get(user_id, [])
        zero_amount_rewards = [r for r in user_rewards if r.tier.amount == 0]
        paid_rewards = [r for r in user_rewards if r.tier.amount > 0]

        for reward in zero_amount_rewards:
            reward.amount = 0
            to_update.append(reward)

        if len(paid_rewards) == len(ledger_entries):
            for reward, entry in zip(paid_rewards, ledger_entries):
                reward.amount = entry.amount
                reward.ledger_entry_id = entry.id
                to_update.append(reward)
        else:
            for reward in paid_rewards:
                reward.amount = reward.tier.amount
                to_update.append(reward)

    UserReward.objects.bulk_update(to_update, ["amount", "ledger_entry"], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ("rewards", "0004_restore_final_approved_reward_amounts"),
        ("wallets", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userreward",
            name="amount",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userreward",
            name="ledger_entry",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wallets.ledgerentry",
            ),
        ),
        migrations.RunPython(backfill_amount_and_ledger_entry, reverse_code=migrations.RunPython.noop),
    ]
