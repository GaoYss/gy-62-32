from django.utils.dateparse import parse_datetime

from backend.appointments.models import Appointment
from backend.appointments.services import serialize_appointment
from backend.common.crud import BaseCRUDService

from .models import VisitRecord


def _serialize_check_out_time(record):
    value = record.check_out_time
    return value.isoformat() if value else None


def _serialize_visitor_temperature(record):
    value = record.visitor_temperature
    if value is not None:
        return str(value)
    return ""


class VisitCRUDService(BaseCRUDService):
    model = VisitRecord
    write_fields = [
        "appointment",
        "appointment_id",
        "check_in_time",
        "check_out_time",
        "visitor_temperature",
        "staff_name",
        "summary",
    ]
    serialize_fields = [
        "id",
        "appointment",
        "appointment_id",
        "check_in_time",
        "check_out_time",
        "visitor_temperature",
        "staff_name",
        "summary",
        "created_at",
        "updated_at",
    ]
    exclude_on_create = {"appointment", "id", "created_at", "updated_at"}
    exclude_on_update = {"appointment", "id", "created_at", "updated_at"}
    select_related = ["appointment", "appointment__resident"]
    relation_fields = {
        "appointment": {"serializer": serialize_appointment, "id_field": "appointment_id"},
    }
    field_serializers = {
        "check_out_time": _serialize_check_out_time,
        "visitor_temperature": _serialize_visitor_temperature,
    }

    def normalize_payload(self, payload):
        data = {field: payload.get(field) for field in self.write_fields if field in payload}
        if "appointment" in data:
            data["appointment_id"] = data.pop("appointment")
        for key in ["check_in_time", "check_out_time"]:
            if key in data and isinstance(data[key], str) and data[key]:
                data[key] = parse_datetime(data[key])
        if data.get("check_out_time") == "":
            data["check_out_time"] = None
        return data

    def validate_related(self, data):
        if "appointment_id" in data:
            Appointment.objects.get(pk=data["appointment_id"])

    def after_create(self, instance, payload):
        instance.appointment.status = "completed"
        instance.appointment.save(update_fields=["status", "updated_at"])


_service = VisitCRUDService()


def serialize_visit(record):
    return _service.serialize(record)


def list_visits():
    return _service.list()


def create_visit(payload):
    return _service.build_instance(payload)


def update_visit(record, payload):
    data = _service.normalize_payload(payload)
    for field, value in data.items():
        if field not in _service.exclude_on_update:
            setattr(record, field, value)
    record.save()
    return record
