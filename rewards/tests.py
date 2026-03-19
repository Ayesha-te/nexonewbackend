from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from .models import RewardTier


class RewardSeedingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_reward_plan_does_not_seed_tiers_on_request(self):
        response = self.client.get("/api/rewards/plan/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        self.assertEqual(RewardTier.objects.count(), 0)

    def test_seed_rewards_command_is_idempotent(self):
        call_command("seed_rewards")
        first_count = RewardTier.objects.count()

        call_command("seed_rewards")
        second_count = RewardTier.objects.count()

        self.assertGreater(first_count, 0)
        self.assertEqual(first_count, second_count)
