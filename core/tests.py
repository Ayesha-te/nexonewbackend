from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

import core.automation as automation
from core.automation import get_automation_status, run_automation_if_needed
from rewards.models import SalaryLog
from withdrawals.services import sync_user_pending_withdrawal
from wallets.services import credit_wallet, ensure_wallet
from withdrawals.models import AutoWithdrawalLog, Withdrawal
from wallets.models import LedgerEntry

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
                "binary_set_income",
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
        self.user.left_team_count = 3
        self.user.right_team_count = 2
        self.user.pair_count = 2
        self.user.auto_pair_income_pairs = 2
        self.user.save(update_fields=["left_team_count", "right_team_count", "pair_count", "auto_pair_income_pairs"])
        credit_wallet(self.user, 400, "binary_set_income", description="Initial binary set income")

    def test_admin_can_approve_pending_withdrawal(self):
        self.client.force_authenticate(self.admin)

        list_response = self.client.get("/api/withdrawals/admin/")
        self.assertEqual(list_response.status_code, 200)
        pending = next((row for row in list_response.data if row["status"] == "pending"), None)

        self.assertIsNotNone(pending)
        self.assertEqual(pending["amount"], 400)
        self.assertEqual(pending["leftTeamTotal"], 3)
        self.assertEqual(pending["rightTeamTotal"], 2)
        self.assertEqual(pending["matchedPairs"], 2)
        self.assertEqual(pending["systemAddedEarnings"], 400)

        approve_response = self.client.post(
            f"/api/withdrawals/admin/{pending['id']}/approve/",
            {"adminAdjustment": 200, "adminNote": "First pair top-up"},
            format="json",
        )
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(approve_response.data["status"], "processed")
        self.assertEqual(approve_response.data["adminAdjustment"], 200)
        self.assertEqual(approve_response.data["finalAmount"], 600)

        self.user.refresh_from_db()
        self.assertEqual(self.user.current_income, 0)
        self.assertEqual(self.user.total_withdrawn, 400)

        my_rows = self.client.get("/api/withdrawals/admin/").data
        processed = next((row for row in my_rows if row["id"] == pending["id"]), None)
        self.assertIsNotNone(processed)
        self.assertEqual(processed["status"], "processed")
        self.assertEqual(processed["adminAdjustment"], 200)
        self.assertEqual(processed["adminNote"], "First pair top-up")


class BinarySetIncomeWithdrawalFlowTests(TestCase):
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

    def test_binary_set_income_uses_normal_withdrawal_pipeline(self):
        credit_wallet(
            self.user,
            400,
            "binary_set_income",
            description="Binary set income #1",
        )

        pending = sync_user_pending_withdrawal(self.user)

        self.assertIsNotNone(pending)
        self.assertEqual(pending.amount, 400)
        self.assertEqual(pending.tax, 20)
        self.assertEqual(pending.net_amount, 380)
        self.assertEqual(pending.tax_type, "normal")


class PairIncomeCorrectionCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="pair-fix@example.com",
            username="pair-fix",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03006666666",
        )
        ensure_wallet(self.user)

    def test_command_reverses_legacy_pair_income_and_updates_pending_withdrawal(self):
        credit_wallet(
            self.user,
            400,
            "binary_set_income",
            description="Valid binary set income",
        )
        credit_wallet(
            self.user,
            400,
            "pair_income",
            description="Legacy duplicate binary income",
        )
        pending = sync_user_pending_withdrawal(self.user)

        self.assertIsNotNone(pending)
        self.assertEqual(pending.amount, 800)

        call_command("fix_pair_income_overpayments", "--apply")

        self.user.refresh_from_db()
        pending.refresh_from_db()
        reversal = LedgerEntry.objects.filter(
            wallet__user=self.user,
            entry_type="pair_income_reversal",
        ).first()

        self.assertIsNotNone(reversal)
        self.assertEqual(reversal.amount, -400)
        self.assertEqual(self.user.current_income, 400)
        self.assertEqual(self.user.wallet.balance, 400)
        self.assertEqual(pending.amount, 400)
