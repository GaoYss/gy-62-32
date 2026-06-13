from django.core.exceptions import ValidationError
from django.db import IntegrityError

from backend.common.crud import make_collection_view, make_detail_view

from .services import NotificationCRUDService


def _notifications_list_params(request):
    active = request.GET.get("active")
    active_value = None if active is None else active.lower() == "true"
    return {"active": active_value}


_notification_exceptions = (ValidationError, IntegrityError, TypeError, ValueError)

notifications_collection = make_collection_view(
    NotificationCRUDService,
    create_exceptions=_notification_exceptions,
    list_params_extractor=_notifications_list_params,
)

notification_detail = make_detail_view(
    NotificationCRUDService,
    update_exceptions=_notification_exceptions,
)
