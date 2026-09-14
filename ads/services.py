from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Count, Sum
from django.utils import timezone

from notifications.services import notify
from wallets.services import credit_wallet

from .models import AdsCycle, AdsSettings, AdVideo, AdWatch

User = get_user_model()

# Small grace window so a device that's a couple of seconds slow reporting completion
# isn't unfairly rejected, without meaningfully opening the door to skipping the ad.
COMPLETION_GRACE_SECONDS = 2
# Upper bound on how long after starting a watch can still be completed, so a stale
# "started" row from days ago can't be replayed to claim a reward.
COMPLETION_MAX_WINDOW_SECONDS = 600


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
    return AdWatch.objects.filter(user=user, watched_date=today, status="completed").count()


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


def _get_eligible_cycle_or_raise(user):
    settings = get_or_create_settings()
    if not settings.enabled:
        raise ValueError("Ads are currently disabled.")

    today = timezone.localdate()
    cycle = (
        AdsCycle.objects.select_for_update()
        .filter(user=user, status="active", end_date__gte=today)
        .order_by("-id")
        .first()
    )
    if cycle is None:
        raise ValueError("No active Ads cycle. Complete a qualifying Binary Pair or wait for your Welcome Ads window.")

    today_count = AdWatch.objects.filter(user=user, watched_date=today, status="completed").count()
    if today_count >= settings.daily_limit:
        raise ValueError("Daily Ads limit reached. Come back tomorrow.")

    return settings, cycle, today, today_count


@transaction.atomic
def start_watch_ad(user):
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    settings, cycle, today, _today_count = _get_eligible_cycle_or_raise(locked_user)

    video = AdVideo.objects.filter(is_active=True).order_by("?").first()
    if video is None:
        raise ValueError("No active ad video is available right now.")

    watch = AdWatch.objects.create(
        user=locked_user,
        cycle=cycle,
        video=video,
        status="started",
        watched_date=today,
        started_at=timezone.now(),
        reward_pkr=0,
    )
    return watch, video, settings


@transaction.atomic
def complete_watch_ad(user, watch_id):
    locked_user = User.objects.select_for_update().get(pk=user.pk)
    try:
        watch = AdWatch.objects.select_for_update().get(pk=watch_id, user=locked_user)
    except AdWatch.DoesNotExist:
        raise ValueError("Ad watch session not found.")

    if watch.status == "completed":
        raise ValueError("This ad has already been recorded.")
    if watch.video is None:
        raise ValueError("This ad video is no longer available. Please start a new ad.")

    elapsed = (timezone.now() - watch.started_at).total_seconds()
    min_required = max(watch.video.duration_seconds - COMPLETION_GRACE_SECONDS, 0)
    if elapsed < min_required:
        raise ValueError("Please watch the full ad before it can be marked complete.")
    if elapsed > watch.video.duration_seconds + COMPLETION_MAX_WINDOW_SECONDS:
        raise ValueError("This ad session has expired. Please start a new ad.")

    settings = get_or_create_settings()
    if not settings.enabled:
        raise ValueError("Ads are currently disabled.")

    cycle = watch.cycle
    today = timezone.localdate()
    if cycle is None or cycle.status != "active" or cycle.end_date < today:
        raise ValueError("Your Ads cycle is no longer active.")

    today_count = (
        AdWatch.objects.filter(user=locked_user, watched_date=today, status="completed")
        .exclude(pk=watch.pk)
        .count()
    )
    if today_count >= settings.daily_limit:
        raise ValueError("Daily Ads limit reached. Come back tomorrow.")

    reward = settings.welcome_reward_pkr if cycle.cycle_type == "welcome" else settings.pair_reward_pkr

    watch.status = "completed"
    watch.completed_at = timezone.now()
    watch.reward_pkr = reward
    watch.save(update_fields=["status", "completed_at", "reward_pkr"])

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


def get_ads_history(user, limit=200):
    rows = (
        AdWatch.objects.filter(user=user, status="completed")
        .select_related("cycle")
        .order_by("-completed_at")[:limit]
    )
    return [
        {
            "id": row.id,
            "date": str(row.watched_date),
            "rewardPkr": row.reward_pkr,
            "cycleType": row.cycle.cycle_type if row.cycle else None,
            "completedAt": row.completed_at.isoformat() if row.completed_at else None,
        }
        for row in rows
    ]


def get_user_ads_earning_total(user):
    return AdWatch.objects.filter(user=user, status="completed").aggregate(total=Sum("reward_pkr"))["total"] or 0


def get_users_ads_earning_totals(user_ids):
    """Batch version of get_user_ads_earning_total — one aggregate query instead of one per
    user, so callers rendering a list (e.g. the admin withdrawals screen) never turn into an
    N+1 loop over users."""
    rows = (
        AdWatch.objects.filter(user_id__in=list(user_ids), status="completed")
        .values("user_id")
        .annotate(total=Sum("reward_pkr"))
    )
    return {row["user_id"]: row["total"] or 0 for row in rows}


def get_daily_ads_payout(day=None):
    day = day or timezone.localdate()
    agg = AdWatch.objects.filter(status="completed", watched_date=day).aggregate(
        total=Sum("reward_pkr"), count=Count("id")
    )
    users_count = (
        AdWatch.objects.filter(status="completed", watched_date=day).values("user_id").distinct().count()
    )
    return {
        "date": str(day),
        "totalPayout": agg["total"] or 0,
        "adsCompleted": agg["count"] or 0,
        "usersCount": users_count,
    }


def get_monthly_ads_payout(month=None):
    month = month or timezone.localdate().strftime("%Y-%m")
    year, month_num = (int(part) for part in month.split("-"))
    qs = AdWatch.objects.filter(status="completed", watched_date__year=year, watched_date__month=month_num)
    agg = qs.aggregate(total=Sum("reward_pkr"), count=Count("id"))
    users_count = qs.values("user_id").distinct().count()
    return {
        "month": month,
        "totalPayout": agg["total"] or 0,
        "adsCompleted": agg["count"] or 0,
        "usersCount": users_count,
    }


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
