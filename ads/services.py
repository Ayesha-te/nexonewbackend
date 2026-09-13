from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from notifications.services import notify
from wallets.services import credit_wallet

from .models import AdsCycle, AdsSettings, AdWatch

User = get_user_model()


def get_or_create_settings():
    return AdsSettings.current()


def get_active_cycle(user):
    today = timezone.localdate()
    return (
        AdsCycle.objects.filter(user=user, status="active", end_date__gte=today)
        .order_by("-id")
        .first()
    )


def get_today_watch_count(user, today=None):
    today = today or timezone.localdate()
    return AdWatch.objects.filter(user=user, watched_date=today).count()


def get_ads_status(user):
    settings = get_or_create_settings()
    cycle = get_active_cycle(user)
    today = timezone.localdate()
    watched_today = get_today_watch_count(user, today=today)
    cycle_type = cycle.cycle_type if cycle else None
    if cycle_type == "welcome":
        reward_per_ad = settings.welcome_reward_pkr
    elif cycle_type == "pair":
        reward_per_ad = settings.pair_reward_pkr
    else:
        reward_per_ad = 0
    remaining_today = max(settings.daily_limit - watched_today, 0)
    can_watch = bool(settings.enabled and cycle is not None and watched_today < settings.daily_limit)
    return {
        "enabled": settings.enabled,
        "cycleType": cycle_type,
        "startDate": cycle.start_date if cycle else None,
        "endDate": cycle.end_date if cycle else None,
        "dailyLimit": settings.daily_limit,
        "watchedToday": watched_today,
        "remainingToday": remaining_today,
        "rewardPerAd": reward_per_ad,
        "canWatch": can_watch,
    }


def on_account_activated(user):
    try:
        settings = get_or_create_settings()
        if not settings.enabled:
            return
        start = timezone.localdate()
        end = start + timedelta(days=settings.welcome_duration_days - 1)
        try:
            with transaction.atomic():
                AdsCycle.objects.create(
                    user=user,
                    cycle_type="welcome",
                    start_date=start,
                    end_date=end,
                    status="active",
                )
        except IntegrityError:
            return
        notify(user, "welcome", start_date=str(start), end_date=str(end))
    except Exception:
        return


@transaction.atomic
def _on_qualifying_pair(user):
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    settings = get_or_create_settings()
    if not settings.enabled:
        return

    notify(locked_user, "pair_completed")

    existing_cycle = (
        AdsCycle.objects.select_for_update().filter(user=locked_user, status="active").first()
    )
    is_renewal = existing_cycle is not None

    if existing_cycle is not None:
        existing_cycle.status = "expired"
        existing_cycle.save(update_fields=["status"])

    today = timezone.localdate()
    end = today + timedelta(days=settings.pair_cycle_days - 1)
    AdsCycle.objects.create(
        user=locked_user,
        cycle_type="pair",
        start_date=today,
        end_date=end,
        status="active",
    )

    notif_type = "ads_cycle_renewed" if is_renewal else "ads_unlocked"
    notify(locked_user, notif_type, start_date=str(today), end_date=str(end))


def on_qualifying_pair(user):
    try:
        _on_qualifying_pair(user)
    except Exception:
        return


@transaction.atomic
def watch_ad(user):
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    settings = get_or_create_settings()
    if not settings.enabled:
        raise ValueError("Ads are currently disabled.")

    today = timezone.localdate()
    cycle = (
        AdsCycle.objects.select_for_update()
        .filter(user=locked_user, status="active", end_date__gte=today)
        .order_by("-id")
        .first()
    )
    if cycle is None:
        raise ValueError("No active Ads cycle. Complete a qualifying Binary Pair or wait for your Welcome Ads window.")

    today_count = AdWatch.objects.filter(user=locked_user, watched_date=today).count()
    if today_count >= settings.daily_limit:
        raise ValueError("Daily Ads limit reached. Come back tomorrow.")

    reward = settings.welcome_reward_pkr if cycle.cycle_type == "welcome" else settings.pair_reward_pkr

    watch = AdWatch.objects.create(
        user=locked_user,
        cycle=cycle,
        watched_date=today,
        reward_pkr=reward,
    )
    credit_wallet(
        locked_user,
        reward,
        "ads_income",
        description=f"Ads reward ({cycle.cycle_type})",
        taxable_type="normal",
    )

    if today_count + 1 == settings.daily_limit:
        notify(locked_user, "daily_ads_completed")

    return watch


def run_daily_ads_maintenance(run_date=None):
    run_date = run_date or timezone.localdate()
    for cycle in AdsCycle.objects.filter(status="active"):
        try:
            if cycle.end_date < run_date:
                cycle.status = "expired"
                if not cycle.expired_notified:
                    notify(cycle.user, "ads_locked")
                    cycle.expired_notified = True
                cycle.save(update_fields=["status", "expired_notified"])
            elif cycle.end_date == run_date + timedelta(days=1) and not cycle.ending_notified:
                notify(cycle.user, "ads_cycle_ending")
                cycle.ending_notified = True
                cycle.save(update_fields=["ending_notified"])
        except Exception:
            continue
