from datetime import timedelta
from threading import Lock

from django.utils import timezone

from rewards.services import process_monthly_salary
from withdrawals.models import AutoWithdrawalLog
from withdrawals.services import process_daily_auto_withdrawals

_automation_lock = Lock()
_last_checked_date = None


def _month_start(value):
    return value.replace(day=1)


def _iter_month_starts(start_date, end_date):
    current = _month_start(start_date)
    end_month = _month_start(end_date)
    while current <= end_month:
        yield current
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)


def get_automation_status():
    today = timezone.localdate()
    last_log = AutoWithdrawalLog.objects.order_by("-run_date").first()
    last_run = last_log.run_date if last_log else None
    pending_days = 0
    if last_run and last_run < today:
        pending_days = (today - last_run).days
    elif last_run is None:
        pending_days = 0
    return {
        "today": today,
        "last_run_date": last_run,
        "ran_today": last_run == today,
        "pending_backfill_days": pending_days,
    }


def run_automation_if_needed():
    global _last_checked_date

    today = timezone.localdate()
    if _last_checked_date == today:
        return False

    with _automation_lock:
        if _last_checked_date == today:
            return False
        last_log = AutoWithdrawalLog.objects.order_by("-run_date").first()
        start_date = last_log.run_date + timedelta(days=1) if last_log else today

        for month_start in _iter_month_starts(start_date, today):
            process_monthly_salary(run_date=month_start)

        current_date = start_date
        while current_date <= today:
            process_daily_auto_withdrawals(run_date=current_date)
            current_date += timedelta(days=1)

        _last_checked_date = today
    return True
