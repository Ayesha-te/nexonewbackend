from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from wallets.services import ensure_wallet

from .models import AdsCycle, AdsSettings, AdVideo, AdWatch
from .services import (
    complete_watch_ad,
    on_account_activated,
    on_qualifying_pair,
    start_watch_ad,
)

User = get_user_model()


class AdsServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="ads-member@example.com",
            username="ads-member",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03001234567",
        )
        ensure_wallet(self.user)
        settings = AdsSettings.current()
        settings.daily_limit = 3
        settings.save(update_fields=["daily_limit"])
        self.video = AdVideo.objects.create(
            title="Test Ad",
            video=SimpleUploadedFile("ad.mp4", b"fake-video-bytes", content_type="video/mp4"),
            duration_seconds=15,
            is_active=True,
        )

    def _full_watch(self):
        watch, video, _settings = start_watch_ad(self.user)
        watch.started_at = timezone.now() - timedelta(seconds=video.duration_seconds + 1)
        watch.save(update_fields=["started_at"])
        return complete_watch_ad(self.user, watch.id)

    def test_fourth_ad_in_one_day_is_rejected(self):
        today = timezone.localdate()
        cycle = AdsCycle.objects.create(
            user=self.user,
            cycle_type="pair",
            start_date=today,
            end_date=today,
            status="active",
        )
        for _ in range(3):
            self._full_watch()

        with self.assertRaises(ValueError):
            start_watch_ad(self.user)

        self.assertEqual(AdWatch.objects.filter(user=self.user, status="completed").count(), 3)
        cycle.refresh_from_db()

    def test_completing_before_video_duration_elapses_is_rejected(self):
        AdsCycle.objects.create(
            user=self.user,
            cycle_type="pair",
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
            status="active",
        )
        watch, _video, _settings = start_watch_ad(self.user)
        with self.assertRaises(ValueError):
            complete_watch_ad(self.user, watch.id)

    def test_on_qualifying_pair_twice_leaves_one_active_cycle(self):
        on_qualifying_pair(self.user)
        on_qualifying_pair(self.user)

        active_cycles = AdsCycle.objects.filter(user=self.user, status="active")
        self.assertEqual(active_cycles.count(), 1)
        self.assertEqual(
            AdsCycle.objects.filter(user=self.user, status="expired").count(), 1
        )
        self.assertEqual(active_cycles.first().cycle_type, "pair")

    def test_watch_ad_without_active_cycle_raises(self):
        with self.assertRaises(ValueError):
            start_watch_ad(self.user)

    def test_on_account_activated_is_idempotent_and_creates_one_welcome_cycle(self):
        on_account_activated(self.user)
        on_account_activated(self.user)

        self.assertEqual(
            AdsCycle.objects.filter(user=self.user, cycle_type="welcome").count(), 1
        )
