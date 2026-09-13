from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Notification, NotificationTypeConfig
from .services import broadcast, notify

User = get_user_model()


def make_user(email, **extra):
    defaults = dict(
        username=email.split("@")[0],
        password="pass12345",
        is_approved=True,
        is_active=True,
        payment_method="easypaisa",
        account_number="03001234567",
    )
    defaults.update(extra)
    return User.objects.create_user(email=email, **defaults)


class NotifyServiceTests(TestCase):
    def test_notify_does_nothing_when_type_disabled(self):
        user = make_user("disabled@example.com")
        NotificationTypeConfig.objects.create(
            notif_type="welcome",
            enabled=False,
            title_template="Hi",
            message_template="Hello",
        )

        notify(user, "welcome")

        self.assertEqual(Notification.objects.filter(user=user).count(), 0)

    def test_notify_does_nothing_when_no_config_exists(self):
        user = make_user("noconfig@example.com")

        notify(user, "welcome")

        self.assertEqual(Notification.objects.filter(user=user).count(), 0)

    def test_notify_falls_back_to_raw_template_on_missing_context_key(self):
        user = make_user("missingkey@example.com")
        NotificationTypeConfig.objects.create(
            notif_type="ads_unlocked",
            enabled=True,
            title_template="Unlocked",
            message_template="From {start_date} to {end_date}",
        )

        notify(user, "ads_unlocked")

        notification = Notification.objects.get(user=user)
        self.assertEqual(notification.message, "From {start_date} to {end_date}")

    def test_notify_renders_context_when_present(self):
        user = make_user("withcontext@example.com")
        NotificationTypeConfig.objects.create(
            notif_type="ads_unlocked",
            enabled=True,
            title_template="Unlocked",
            message_template="From {start_date} to {end_date}",
        )

        notify(user, "ads_unlocked", start_date="2026-01-01", end_date="2026-01-04")

        notification = Notification.objects.get(user=user)
        self.assertEqual(notification.message, "From 2026-01-01 to 2026-01-04")

    def test_notify_never_raises(self):
        user = make_user("noraise@example.com")
        NotificationTypeConfig.objects.create(
            notif_type="welcome",
            enabled=True,
            title_template="Hi",
            message_template="Hello",
        )
        # Passing a non-user object should not raise even though it will fail
        # inside Notification.objects.create().
        notify(None, "welcome")
        self.assertTrue(True)


class BroadcastServiceTests(TestCase):
    def test_broadcast_to_all_creates_one_per_non_staff_user(self):
        member1 = make_user("member1@example.com")
        member2 = make_user("member2@example.com")
        staff = make_user("staffmember@example.com", is_staff=True)

        sent = broadcast("Title", "Message", user_ids="all")

        self.assertEqual(sent, 2)
        self.assertEqual(Notification.objects.filter(user=member1).count(), 1)
        self.assertEqual(Notification.objects.filter(user=member2).count(), 1)
        self.assertEqual(Notification.objects.filter(user=staff).count(), 0)

    def test_broadcast_to_specific_ids(self):
        member1 = make_user("target1@example.com")
        member2 = make_user("target2@example.com")

        sent = broadcast("Title", "Message", user_ids=[member1.id])

        self.assertEqual(sent, 1)
        self.assertEqual(Notification.objects.filter(user=member1).count(), 1)
        self.assertEqual(Notification.objects.filter(user=member2).count(), 0)


class NotificationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user("apiuser@example.com")
        self.other_user = make_user("otheruser@example.com")
        self.client.force_authenticate(self.user)

    def test_marking_one_notification_read_does_not_affect_others(self):
        n1 = Notification.objects.create(user=self.user, notif_type="welcome", title="A", message="a")
        n2 = Notification.objects.create(user=self.user, notif_type="welcome", title="B", message="b")

        response = self.client.post(f"/api/notifications/me/{n1.id}/read/")

        self.assertEqual(response.status_code, 200)
        n1.refresh_from_db()
        n2.refresh_from_db()
        self.assertTrue(n1.is_read)
        self.assertFalse(n2.is_read)

    def test_read_all_marks_all_unread_for_user(self):
        Notification.objects.create(user=self.user, notif_type="welcome", title="A", message="a")
        Notification.objects.create(user=self.user, notif_type="welcome", title="B", message="b")

        response = self.client.post("/api/notifications/me/read-all/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["updated"], 2)
        self.assertEqual(self.user.notifications.filter(is_read=False).count(), 0)

    def test_user_cannot_mark_another_users_notification_read(self):
        other_notification = Notification.objects.create(
            user=self.other_user, notif_type="welcome", title="A", message="a"
        )

        response = self.client.post(f"/api/notifications/me/{other_notification.id}/read/")

        self.assertEqual(response.status_code, 404)
        other_notification.refresh_from_db()
        self.assertFalse(other_notification.is_read)

    def test_my_notifications_returns_results_and_unread_count(self):
        Notification.objects.create(user=self.user, notif_type="welcome", title="A", message="a")
        Notification.objects.create(
            user=self.user, notif_type="welcome", title="B", message="b", is_read=True
        )

        response = self.client.get("/api/notifications/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["unreadCount"], 1)
