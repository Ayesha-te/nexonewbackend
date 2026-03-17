from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

import core.automation as automation
from core.automation import get_automation_status, run_automation_if_needed
from rewards.models import SalaryLog
from withdrawals.services import sync_user_pending_withdrawal
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
        self.assertEqual(withdrawals.first().status, "pending")
        self.assertEqual(AutoWithdrawalLog.objects.filter(run_date__gte=start_date).count(), 4)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_withdrawn, 0)

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


class WithdrawalApprovalApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="admin2@example.com",
            username="admin2",
            password="adminpass123",
        )
        self.user = User.objects.create_user(
            email="member2@example.com",
            username="member2",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03000000000",
        )
        credit_wallet(self.user, 400, "pair_income", description="Initial pair income")

    def test_admin_can_approve_pending_withdrawal(self):
        self.client.force_authenticate(self.admin)

        list_response = self.client.get("/api/withdrawals/admin/")
        self.assertEqual(list_response.status_code, 200)
        pending = next((row for row in list_response.data if row["status"] == "pending"), None)

        self.assertIsNotNone(pending)
        self.assertEqual(pending["amount"], 400)

        approve_response = self.client.post(f"/api/withdrawals/admin/{pending['id']}/approve/")
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(approve_response.data["status"], "processed")

        self.user.refresh_from_db()
        self.assertEqual(self.user.current_income, 0)
        self.assertEqual(self.user.total_withdrawn, 400)

        my_rows = self.client.get("/api/withdrawals/admin/").data
        processed = next((row for row in my_rows if row["id"] == pending["id"]), None)
        self.assertIsNotNone(processed)
        self.assertEqual(processed["status"], "processed")


class ReferralIncomeWithdrawalFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="referral-flow@example.com",
            username="referral-flow",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03005555555",
        )
        ensure_wallet(self.user)

    def test_referral_pair_income_uses_normal_withdrawal_pipeline(self):
        credit_wallet(
            self.user,
            400,
            "referral_pair_income",
            description="Referral pair income #1",
        )

        pending = sync_user_pending_withdrawal(self.user)

        self.assertIsNotNone(pending)
        self.assertEqual(pending.amount, 400)
        self.assertEqual(pending.tax, 20)
        self.assertEqual(pending.net_amount, 380)
        self.assertEqual(pending.tax_type, "normal")
