from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class BinaryNode(models.Model):
    user = models.OneToOneField(User, related_name="binary_node", on_delete=models.CASCADE)
    parent = models.ForeignKey(User, related_name="children_nodes", null=True, blank=True, on_delete=models.CASCADE)
    side = models.CharField(max_length=5, choices=(("left", "Left"), ("right", "Right"), ("root", "Root")), default="root")
    created_at = models.DateTimeField(default=timezone.now)
