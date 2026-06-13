from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError

from backend.common.crud import make_collection_view, make_detail_view

from .services import AppointmentCRUDService


def _appointments_list_params(request):
    return {"status": request.GET.get("status")}


appointments_collection = make_collection_view(
    AppointmentCRUDService,
    create_exceptions=(ObjectDoesNotExist, ValidationError, IntegrityError, KeyError, TypeError, ValueError),
    list_params_extractor=_appointments_list_params,
)

appointment_detail = make_detail_view(
    AppointmentCRUDService,
    update_exceptions=(ObjectDoesNotExist, ValidationError, IntegrityError, TypeError, ValueError),
)
