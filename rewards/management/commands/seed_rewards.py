from django.core.management.base import BaseCommand

from rewards.services import seed_reward_tiers


class Command(BaseCommand):
    help = "Seed reward tiers once."

    def handle(self, *args, **options):
        seed_reward_tiers()
        self.stdout.write(self.style.SUCCESS("Reward tiers seeded successfully."))
