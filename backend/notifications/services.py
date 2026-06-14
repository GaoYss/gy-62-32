from backend.common.crud import BaseCRUDService

from .models import EmergencyNotification


class NotificationCRUDService(BaseCRUDService):
    model = EmergencyNotification
    write_fields = ["title", "content", "level", "target_group", "is_active"]
    serialize_fields = [
        "id",
        "title",
        "content",
        "level",
        "target_group",
        "is_active",
        "published_at",
        "updated_at",
    ]
    exclude_on_create = {"id", "published_at", "updated_at"}
    exclude_on_update = {"id", "published_at", "updated_at"}

    def filter_queryset(self, queryset, params):
        active = params.get("active")
        if active is not None:
            queryset = queryset.filter(is_active=active)
        return queryset


_service = NotificationCRUDService()


def serialize_notification(notification):
    return _service.serialize(notification)


def list_notifications(active=None):
    return _service.list({"active": active})


def create_notification(payload):
    return _service.create(payload)


def update_notification(notification, payload):
    return _service.update(notification, payload)
