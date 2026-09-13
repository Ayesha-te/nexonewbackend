from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Attendance
from .services import get_monthly_ranking, get_user_history, mark_attendance

User = get_user_model()


def make_user(email, **extra):
    defaults = {
        "username": email.split("@")[0],
        "password": "pass12345",
        "is_approved": True,
        "is_active": True,
        "payment_method": "easypaisa",
        "account_number": "03001234567",
    }
    defaults.update(extra)
    return User.objects.create_user(email=email, **defaults)


class MarkAttendanceServiceTests(TestCase):
    def setUp(self):
        self.user = make_user("member@example.com")

    def test_marking_attendance_twice_same_day_does_not_duplicate(self):
        today = timezone.localdate()

        attendance1, created1 = mark_attendance(self.user, today=today)
        attendance2, created2 = mark_attendance(self.user, today=today)

        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(attendance1.pk, attendance2.pk)
        self.assertEqual(Attendance.objects.filter(user=self.user, date=today).count(), 1)


class AttendanceStreakTests(TestCase):
    def setUp(self):
        self.user = make_user("member2@example.com")

    def test_three_consecutive_days_gives_streak_of_three(self):
        today = timezone.localdate()
        for offset in range(3):
            Attendance.objects.create(user=self.user, date=today - timedelta(days=offset))

        history = get_user_history(self.user)
        self.assertEqual(history["currentStreak"], 3)

    def test_gap_breaks_streak(self):
        today = timezone.localdate()
        Attendance.objects.create(user=self.user, date=today)
        Attendance.objects.create(user=self.user, date=today - timedelta(days=1))
        # gap at 2 days ago
        Attendance.objects.create(user=self.user, date=today - timedelta(days=3))

        history = get_user_history(self.user)
        self.assertEqual(history["currentStreak"], 2)


class MonthlyRankingTests(TestCase):
    def test_users_bucketed_into_correct_tiers(self):
        month = timezone.localdate().strftime("%Y-%m")
        year, month_num = [int(part) for part in month.split("-")]

        user_27 = make_user("u27@example.com")
        user_26 = make_user("u26@example.com")
        user_24 = make_user("u24@example.com")
        user_19 = make_user("u19@example.com")

        def mark_days(user, count):
            for day in range(1, count + 1):
                Attendance.objects.create(user=user, date=timezone.datetime(year, month_num, day).date())

        mark_days(user_27, 27)
        mark_days(user_26, 26)
        mark_days(user_24, 24)
        mark_days(user_19, 19)

        ranking = get_monthly_ranking(month)

        tier_27_ids = {row["userId"] for row in ranking["tiers"]["27+"]}
        tier_25_26_ids = {row["userId"] for row in ranking["tiers"]["25-26"]}
        tier_20_24_ids = {row["userId"] for row in ranking["tiers"]["20-24"]}

        self.assertIn(user_27.id, tier_27_ids)
        self.assertIn(user_26.id, tier_25_26_ids)
        self.assertIn(user_24.id, tier_20_24_ids)
        self.assertNotIn(user_19.id, tier_27_ids | tier_25_26_ids | tier_20_24_ids)


class AdminAttendanceEndpointPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user("nonadmin@example.com")
        self.client.force_authenticate(self.user)

    def test_admin_today_view_rejects_non_admin(self):
        response = self.client.get("/api/attendance/admin/today/")
        self.assertIn(response.status_code, (401, 403))

    def test_admin_ranking_view_rejects_non_admin(self):
        response = self.client.get("/api/attendance/admin/ranking/")
        self.assertIn(response.status_code, (401, 403))

    def test_admin_user_view_rejects_non_admin(self):
        response = self.client.get(f"/api/attendance/admin/user/{self.user.pk}/")
        self.assertIn(response.status_code, (401, 403))
