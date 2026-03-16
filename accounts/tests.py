from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from pins.models import Pin

User = get_user_model()


class ActivateUserViewTests(TestCase):
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
        self.client.force_authenticate(self.user)

    def test_pin_is_not_consumed_when_activation_request_fails_validation(self):
        pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)

        response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": pin.code,
                "firstName": "Ali",
                "lastName": "Khan",
                "email": "",
                "phone": "03001234567",
                "accountNumber": "03001234567",
                "referralEmail": self.user.email,
                "position": "left",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )

        pin.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(pin.status, "unused")
        self.assertIsNone(pin.used_by)

    def test_pin_is_marked_used_only_after_successful_activation(self):
        pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)

        response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": pin.code,
                "firstName": "Ali",
                "lastName": "Khan",
                "email": "child@example.com",
                "phone": "03007654321",
                "accountNumber": "03007654321",
                "referralEmail": self.user.email,
                "position": "left",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )

        pin.refresh_from_db()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(pin.status, "used")
        self.assertIsNotNone(pin.used_by)
        self.assertEqual(pin.used_by.email, "child@example.com")
