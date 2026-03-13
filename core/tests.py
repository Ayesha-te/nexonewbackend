from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

import core.automation as automation
from core.automation import get_automation_status, run_automation_if_needed
from rewards.models import SalaryLog
from wallets.services import credit_wallet, ensure_wallet
from withdrawals.models import AutoWithdrawalLog, Withdrawal

User = get_user_model()


class AutomationCatchupTests(TestCase):
    def setUp(self):
        automation._last_checked_date = None
        self.user = User.objects.create_user(
            email="member@example.com",
            username="member",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03001234567",
        )
        ensure_wallet(self.user)

    def test_backfills_missed_daily_withdrawals(self):
        today = timezone.localdate()
        start_date = today - timedelta(days=3)

        for offset in range(4):
            credit_wallet(
                self.user,
                1000,
                "pair_income",
                description=f"Income for day {offset + 1}",
            )

        AutoWithdrawalLog.objects.create(run_date=start_date - timedelta(days=1))

        run_automation_if_needed()

        withdrawals = Withdrawal.objects.filter(user=self.user).order_by("date")
        self.assertEqual(withdrawals.count(), 1)
        self.assertEqual(withdrawals.first().date, start_date)
        self.assertEqual(AutoWithdrawalLog.objects.filter(run_date__gte=start_date).count(), 4)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_withdrawn, 4000)

    def test_backfills_monthly_salary_for_missed_months(self):
        today = timezone.localdate()
        self.user.pair_count = 50000
        self.user.save(update_fields=["pair_count"])
        previous_month_end = today.replace(day=1) - timedelta(days=1)
        old_run_date = previous_month_end.replace(day=1) - timedelta(days=1)
        AutoWithdrawalLog.objects.create(run_date=old_run_date)

        run_automation_if_needed()

        salary_months = list(SalaryLog.objects.filter(user=self.user).values_list("month", flat=True))
        self.assertGreaterEqual(len(salary_months), 2)
        self.assertIn(previous_month_end.strftime("%Y-%m"), salary_months)
        self.assertIn(today.strftime("%Y-%m"), salary_months)


class AutomationStatusApiTests(TestCase):
    def setUp(self):
        automation._last_checked_date = None
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass123",
        )

    def test_admin_system_status_endpoint_returns_latest_state(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/accounts/admin/system-status/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("lastAutomationRun", response.data)
        self.assertIn("pendingBackfillDays", response.data)
        self.assertTrue(response.data["ranToday"])
        self.assertEqual(get_automation_status()["pending_backfill_days"], 0)
