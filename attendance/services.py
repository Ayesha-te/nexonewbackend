from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from .models import Attendance

User = get_user_model()


def mark_attendance(user, today=None):
    today = today or timezone.localdate()
    attendance, created = Attendance.objects.get_or_create(
        user=user, date=today, defaults={"marked_at": timezone.now()}
    )
    return attendance, created


def _parse_month(month):
    year_str, month_str = month.split("-")
    return int(year_str), int(month_str)


def _current_streak(user, today):
    marked_dates = set(
        Attendance.objects.filter(user=user).values_list("date", flat=True)
    )

    if today in marked_dates:
        cursor = today
    else:
        cursor = today - timedelta(days=1)

    streak = 0
    while cursor in marked_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def get_user_history(user, month=None):
    queryset = Attendance.objects.filter(user=user)
    if month:
        year, month_num = _parse_month(month)
        queryset = queryset.filter(date__year=year, date__month=month_num)
    records = queryset.order_by("-date")

    today = timezone.localdate()
    return {
        "records": list(records),
        "totalDays": records.count(),
        "currentStreak": _current_streak(user, today),
    }


def get_monthly_summary(user, month=None):
    month = month or timezone.localdate().strftime("%Y-%m")
    year, month_num = _parse_month(month)
    present_days = Attendance.objects.filter(
        user=user, date__year=year, date__month=month_num
    ).count()

    if present_days >= 27:
        category = "27+"
    elif present_days >= 25:
        category = "25-26"
    elif present_days >= 20:
        category = "20-24"
    else:
        category = None

    return {"month": month, "presentDays": present_days, "category": category}


def get_today_attendance_list():
    today = timezone.localdate()
    rows_qs = (
        Attendance.objects.filter(date=today)
        .select_related("user")
        .order_by("marked_at")
    )
    rows = [
        {
            "userId": attendance.user_id,
            "userName": attendance.user.full_name,
            "email": attendance.user.email,
            "phone": attendance.user.phone,
            "markedAt": attendance.marked_at.isoformat(),
        }
        for attendance in rows_qs
    ]
    return {"date": str(today), "total": len(rows), "rows": rows}


def get_monthly_ranking(month=None):
    month = month or timezone.localdate().strftime("%Y-%m")
    year, month_num = _parse_month(month)

    counts = (
        Attendance.objects.filter(date__year=year, date__month=month_num, user__is_staff=False)
        .values("user")
        .annotate(days=Count("id"))
    )
    user_ids = [row["user"] for row in counts]
    days_by_user_id = {row["user"]: row["days"] for row in counts}
    users_by_id = {user.id: user for user in User.objects.filter(id__in=user_ids)}

    tiers = {"27+": [], "25-26": [], "20-24": []}
    summary = {"20+": 0, "25+": 0, "27+": 0}

    for user_id, present_days in days_by_user_id.items():
        user = users_by_id.get(user_id)
        if user is None:
            continue

        if present_days >= 20:
            summary["20+"] += 1
        if present_days >= 25:
            summary["25+"] += 1
        if present_days >= 27:
            summary["27+"] += 1

        row = {
            "userId": user.id,
            "userName": user.full_name,
            "email": user.email,
            "presentDays": present_days,
        }
        if present_days >= 27:
            tiers["27+"].append(row)
        elif present_days >= 25:
            tiers["25-26"].append(row)
        elif present_days >= 20:
            tiers["20-24"].append(row)

    for tier_rows in tiers.values():
        tier_rows.sort(key=lambda row: row["presentDays"], reverse=True)

    return {"month": month, "tiers": tiers, "summary": summary}
