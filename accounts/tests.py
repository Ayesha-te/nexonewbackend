from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from complaints.models import ComplaintFeedback
from network.models import BinaryNode
from pins.models import Pin
from wallets.models import LedgerEntry
from wallets.services import ensure_wallet

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

    def test_sponsor_is_not_paid_after_only_one_binary_side_activation(self):
        pin = Pin.objects.create(owner=self.user, status="unused", amount=1500)

        response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": pin.code,
                "firstName": "Ali",
                "lastName": "Khan",
                "email": "bonus-child@example.com",
                "phone": "03007654321",
                "accountNumber": "03007654321",
                "referralEmail": self.user.email,
                "position": "left",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.user.refresh_from_db()
        pair_entry = LedgerEntry.objects.filter(
            wallet__user=self.user,
            entry_type="binary_set_income",
        ).first()

        self.assertEqual(self.user.current_income, 0)
        self.assertIsNone(pair_entry)

    def test_sponsor_is_not_paid_when_two_users_join_on_same_side_only(self):
        first_pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)
        second_pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)

        first_response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": first_pin.code,
                "firstName": "First",
                "lastName": "Left",
                "email": "same-left-1@example.com",
                "phone": "03117654321",
                "accountNumber": "03117654321",
                "referralEmail": self.user.email,
                "position": "left",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )
        second_response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": second_pin.code,
                "firstName": "Second",
                "lastName": "Left",
                "email": "same-left-2@example.com",
                "phone": "03117654322",
                "accountNumber": "03117654322",
                "referralEmail": self.user.email,
                "position": "left",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)

        self.user.refresh_from_db()
        pair_entry = LedgerEntry.objects.filter(
            wallet__user=self.user,
            entry_type="binary_set_income",
        ).first()

        self.assertEqual(self.user.left_team_count, 2)
        self.assertEqual(self.user.right_team_count, 0)
        self.assertEqual(self.user.pair_count, 0)
        self.assertEqual(self.user.current_income, 0)
        self.assertIsNone(pair_entry)

    def test_sponsor_gets_first_binary_set_income_when_left_and_right_match(self):
        first_pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)
        second_pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)

        first_response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": first_pin.code,
                "firstName": "First",
                "lastName": "User",
                "email": "set-left@example.com",
                "phone": "03330000001",
                "accountNumber": "03330000001",
                "referralEmail": self.user.email,
                "position": "left",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )
        second_response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": second_pin.code,
                "firstName": "Second",
                "lastName": "User",
                "email": "set-right@example.com",
                "phone": "03330000002",
                "accountNumber": "03330000002",
                "referralEmail": self.user.email,
                "position": "right",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)

        self.user.refresh_from_db()
        pair_entries = LedgerEntry.objects.filter(
            wallet__user=self.user,
            entry_type="binary_set_income",
        )

        self.assertEqual(self.user.left_team_count, 1)
        self.assertEqual(self.user.right_team_count, 1)
        self.assertEqual(self.user.pair_count, 1)
        self.assertEqual(self.user.auto_pair_income_pairs, 1)
        self.assertEqual(self.user.current_income, 400)
        self.assertEqual(pair_entries.count(), 1)
        self.assertEqual(pair_entries.first().amount, 400)

    def test_repeated_left_placements_stay_on_left_chain(self):
        first_pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)
        second_pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)

        first_response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": first_pin.code,
                "firstName": "Ali",
                "lastName": "Khan",
                "email": "left1@example.com",
                "phone": "03001111111",
                "accountNumber": "03001111111",
                "referralEmail": self.user.email,
                "position": "left",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )
        second_response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": second_pin.code,
                "firstName": "Sara",
                "lastName": "Khan",
                "email": "left2@example.com",
                "phone": "03002222222",
                "accountNumber": "03002222222",
                "referralEmail": self.user.email,
                "position": "left",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)

        first_child = User.objects.get(email="left1@example.com")
        second_child = User.objects.get(email="left2@example.com")

        first_node = BinaryNode.objects.get(user=first_child)
        second_node = BinaryNode.objects.get(user=second_child)

        self.assertEqual(first_node.parent, self.user)
        self.assertEqual(first_node.side, "left")
        self.assertEqual(second_node.parent, first_child)
        self.assertEqual(second_node.side, "left")

    def test_four_repeated_left_placements_stay_on_single_left_chain(self):
        created_emails = []

        for index in range(4):
            pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)
            email = f"left-chain-{index + 1}@example.com"
            response = self.client.post(
                "/api/accounts/activate/",
                {
                    "pinToken": pin.code,
                    "firstName": f"Left{index + 1}",
                    "lastName": "Chain",
                    "email": email,
                    "phone": f"0300000000{index + 1}",
                    "accountNumber": f"0300000000{index + 1}",
                    "referralEmail": self.user.email,
                    "position": "left",
                    "paymentMethod": "easypaisa",
                },
                format="json",
            )
            self.assertEqual(response.status_code, 201)
            created_emails.append(email)

        parent = self.user
        for email in created_emails:
            child = User.objects.get(email=email)
            node = BinaryNode.objects.get(user=child)
            self.assertEqual(node.parent, parent)
            self.assertEqual(node.side, "left")
            parent = child

        self.user.refresh_from_db()
        self.assertEqual(self.user.left_team_count, 4)
        self.assertEqual(self.user.right_team_count, 0)

    def test_four_repeated_right_placements_stay_on_single_right_chain(self):
        created_emails = []

        for index in range(4):
            pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)
            email = f"right-chain-{index + 1}@example.com"
            response = self.client.post(
                "/api/accounts/activate/",
                {
                    "pinToken": pin.code,
                    "firstName": f"Right{index + 1}",
                    "lastName": "Chain",
                    "email": email,
                    "phone": f"0310000000{index + 1}",
                    "accountNumber": f"0310000000{index + 1}",
                    "referralEmail": self.user.email,
                    "position": "right",
                    "paymentMethod": "easypaisa",
                },
                format="json",
            )
            self.assertEqual(response.status_code, 201)
            created_emails.append(email)

        parent = self.user
        for email in created_emails:
            child = User.objects.get(email=email)
            node = BinaryNode.objects.get(user=child)
            self.assertEqual(node.parent, parent)
            self.assertEqual(node.side, "right")
            parent = child

        self.user.refresh_from_db()
        self.assertEqual(self.user.left_team_count, 0)
        self.assertEqual(self.user.right_team_count, 4)

    def test_activation_can_place_user_under_different_referral_email_on_selected_side(self):
        sponsor = User.objects.create_user(
            email="sponsor@example.com",
            username="sponsor",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03220000000",
        )
        pin = Pin.objects.create(owner=self.user, status="unused", amount=1000)

        response = self.client.post(
            "/api/accounts/activate/",
            {
                "pinToken": pin.code,
                "firstName": "Right",
                "lastName": "Child",
                "email": "right-child@example.com",
                "phone": "03221111111",
                "accountNumber": "03221111111",
                "referralEmail": sponsor.email,
                "position": "right",
                "paymentMethod": "easypaisa",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        created_user = User.objects.get(email="right-child@example.com")
        created_node = BinaryNode.objects.get(user=created_user)
        pin.refresh_from_db()
        sponsor.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(created_user.referred_by, sponsor)
        self.assertEqual(created_user.placement_parent, sponsor)
        self.assertEqual(created_user.placement_side, "right")
        self.assertEqual(created_node.parent, sponsor)
        self.assertEqual(created_node.side, "right")
        self.assertEqual(pin.used_by, created_user)
        self.assertEqual(sponsor.current_income, 0)
        self.assertEqual(sponsor.right_team_count, 1)
        self.assertEqual(self.user.right_team_count, 0)


class AdminDeleteUserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="admin-delete@example.com",
            username="admin-delete",
            password="adminpass123",
        )
        self.root = User.objects.create_user(
            email="root@example.com",
            username="root",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03000000001",
        )
        self.left = User.objects.create_user(
            email="left@example.com",
            username="left",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03000000002",
            referred_by=self.root,
            placement_parent=self.root,
            placement_side="left",
        )
        self.right = User.objects.create_user(
            email="right@example.com",
            username="right",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03000000003",
            referred_by=self.root,
            placement_parent=self.root,
            placement_side="right",
        )
        self.left_child = User.objects.create_user(
            email="left-child@example.com",
            username="leftchild",
            password="pass12345",
            is_approved=True,
            is_active=True,
            payment_method="easypaisa",
            account_number="03000000004",
            referred_by=self.left,
            placement_parent=self.left,
            placement_side="left",
        )

        BinaryNode.objects.create(user=self.left, parent=self.root, side="left")
        BinaryNode.objects.create(user=self.right, parent=self.root, side="right")
        BinaryNode.objects.create(user=self.left_child, parent=self.left, side="left")
        ensure_wallet(self.root)
        ensure_wallet(self.left)
        ensure_wallet(self.right)
        ensure_wallet(self.left_child)
        ComplaintFeedback.objects.create(user=self.left, message="Test", type="feedback")

        self.root.left_team_count = 2
        self.root.right_team_count = 1
        self.root.pair_count = 1
        self.root.save(update_fields=["left_team_count", "right_team_count", "pair_count"])
        self.left.left_team_count = 1
        self.left.save(update_fields=["left_team_count"])

        self.client.force_authenticate(self.admin)

    def test_admin_can_delete_user_and_entire_subtree(self):
        response = self.client.delete(f"/api/accounts/admin/users/{self.left.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deletedCount"], 2)
        self.assertFalse(User.objects.filter(id=self.left.id).exists())
        self.assertFalse(User.objects.filter(id=self.left_child.id).exists())
        self.assertFalse(BinaryNode.objects.filter(user_id=self.left.id).exists())
        self.assertFalse(BinaryNode.objects.filter(user_id=self.left_child.id).exists())
        self.assertFalse(ComplaintFeedback.objects.filter(user_id=self.left.id).exists())

        self.root.refresh_from_db()
        self.right.refresh_from_db()
        self.assertEqual(self.root.left_team_count, 0)
        self.assertEqual(self.root.right_team_count, 1)
        self.assertEqual(self.root.pair_count, 0)
        self.assertEqual(self.right.referred_by, self.root)
