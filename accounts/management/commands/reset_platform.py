from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Permanently deletes every non-staff user account and all of their data "
        "(binary tree position, pins, withdrawals, rewards, ads history, attendance, "
        "complaints/feedback, wallet/ledger entries) via cascade. Staff/admin accounts "
        "are kept. This is irreversible - there is no undo and no backup is taken by "
        "this command. Pass --yes to actually run it; otherwise it only reports what "
        "would be deleted."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Actually perform the deletion. Without this flag, only a dry-run count is printed.",
        )

    def handle(self, *args, **options):
        queryset = User.objects.filter(is_staff=False)
        count = queryset.count()

        if not options["yes"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {count} non-staff user account(s) would be permanently deleted. "
                    "Re-run with --yes to actually delete them."
                )
            )
            return

        with transaction.atomic():
            deleted_count, _ = queryset.delete()

        self.stdout.write(self.style.SUCCESS(f"Deleted {count} user account(s) and all related records."))
