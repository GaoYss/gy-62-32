from django.utils.dateparse import parse_datetime

from backend.common.crud import BaseCRUDService
from backend.residents.models import Resident
from backend.residents.services import serialize_resident

from .models import Appointment


class AppointmentCRUDService(BaseCRUDService):
    model = Appointment
    write_fields = [
        "resident",
        "resident_id",
        "family_name",
        "family_phone",
        "relationship",
        "visit_time",
        "visitor_count",
        "status",
        "notes",
    ]
    serialize_fields = [
        "id",
        "resident",
        "resident_id",
        "family_name",
        "family_phone",
        "relationship",
        "visit_time",
        "visitor_count",
        "status",
        "notes",
        "created_at",
        "updated_at",
    ]
    exclude_on_create = {"resident", "id", "created_at", "updated_at"}
    exclude_on_update = {"resident", "id", "created_at", "updated_at"}
    select_related = ["resident"]
    relation_fields = {
        "resident": {"serializer": serialize_resident, "id_field": "resident_id"},
    }

    def filter_queryset(self, queryset, params):
        status = params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def normalize_payload(self, payload):
        data = {field: payload.get(field) for field in self.write_fields if field in payload}
        if "resident" in data:
            data["resident_id"] = data.pop("resident")
        if "visit_time" in data and isinstance(data["visit_time"], str):
            data["visit_time"] = parse_datetime(data["visit_time"])
        return data

    def validate_related(self, data):
        if "resident_id" in data:
            Resident.objects.get(pk=data["resident_id"])


_service = AppointmentCRUDService()


def serialize_appointment(appointment):
    return _service.serialize(appointment)


def list_appointments(status=None):
    return _service.list({"status": status} if status else {})


def create_appointment(payload):
    return _service.create(payload)


def update_appointment(appointment, payload):
    return _service.update(appointment, payload)
