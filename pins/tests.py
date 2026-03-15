from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from pins.models import Pin

User = get_user_model()


class MyPinsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="member@example.com",
            username="member",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03001234567",
        )
        self.used_by_user = User.objects.create_user(
            email="child@example.com",
            username="child",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03007654321",
        )
        self.client.force_authenticate(self.user)

    def test_my_pins_returns_used_and_unused_pins(self):
        available_pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)
        used_pin = Pin.objects.create(owner=self.user, status="used", used_by=self.used_by_user, amount=1000)

        response = self.client.get("/api/pins/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        returned_ids = {row["id"] for row in response.data}
        returned_statuses = {row["id"]: row["status"] for row in response.data}
        self.assertEqual(returned_ids, {available_pin.id, used_pin.id})
        self.assertEqual(returned_statuses[available_pin.id], "available")
        self.assertEqual(returned_statuses[used_pin.id], "used")

    def test_accounts_me_available_pins_only_counts_unused_pins(self):
        Pin.objects.create(owner=self.user, status="unused", amount=1000)
        Pin.objects.create(owner=self.user, status="used", used_by=self.used_by_user, amount=1000)

        response = self.client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["available_pins"], 1)
