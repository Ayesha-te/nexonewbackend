from django.conf import settings

from .models import Notification, NotificationTypeConfig

User = settings.AUTH_USER_MODEL


def notify(user, notif_type: str, **context) -> None:
    """
    Look up NotificationTypeConfig for notif_type and, if enabled, create a
    Notification for user with the rendered title/message.

    This function must NEVER raise - callers (ads app, attendance app, account
    activation, etc.) must never fail because notifications broke.
    """
    try:
        config = NotificationTypeConfig.objects.filter(notif_type=notif_type).first()
        if config is None or not config.enabled:
            return

        try:
            title = config.title_template.format(**context)
        except Exception:
            title = config.title_template

        try:
            message = config.message_template.format(**context)
        except Exception:
            message = config.message_template

        Notification.objects.create(
            user=user,
            notif_type=notif_type,
            title=title,
            message=message,
            is_read=False,
        )
    except Exception:
        return


def broadcast(title, message, user_ids="all"):
    """
    Create one admin_custom Notification per targeted user.

    - user_ids == "all": all non-staff users.
    - otherwise: non-staff users whose id is in user_ids.

    Returns the number of Notification rows created.
    """
    from django.contrib.auth import get_user_model

    UserModel = get_user_model()

    if user_ids == "all":
        targets = UserModel.objects.filter(is_staff=False)
    else:
        targets = UserModel.objects.filter(id__in=user_ids, is_staff=False)

    notifications = [
        Notification(
            user=user,
            notif_type="admin_custom",
            title=title,
            message=message,
            is_read=False,
        )
        for user in targets
    ]
    created = Notification.objects.bulk_create(notifications)
    return len(created)
