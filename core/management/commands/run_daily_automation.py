from django.core.management.base import BaseCommand

from rewards.services import process_monthly_salary
from withdrawals.services import process_daily_auto_withdrawals


class Command(BaseCommand):
    help = "Run daily automatic MLM jobs."

    def handle(self, *args, **options):
        withdrawals = process_daily_auto_withdrawals()
        salaries = process_monthly_salary()
        self.stdout.write(
            self.style.SUCCESS(
                f"Automation complete. Auto withdrawals: {withdrawals}, salary credits: {salaries}"
            )
        )
