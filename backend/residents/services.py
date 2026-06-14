from backend.common.crud import BaseCRUDService

from .models import Resident


class ResidentCRUDService(BaseCRUDService):
    model = Resident
    write_fields = [
        "name",
        "gender",
        "age",
        "room_number",
        "care_level",
        "emergency_contact",
        "emergency_phone",
        "medical_notes",
    ]
    serialize_fields = [
        "id",
        "name",
        "gender",
        "age",
        "room_number",
        "care_level",
        "emergency_contact",
        "emergency_phone",
        "medical_notes",
        "created_at",
        "updated_at",
    ]
    exclude_on_create = {"id", "created_at", "updated_at"}
    exclude_on_update = {"id", "created_at", "updated_at"}


_service = ResidentCRUDService()


def serialize_resident(resident):
    return _service.serialize(resident)


def list_residents():
    return _service.list()


def create_resident(payload):
    return _service.create(payload)


def update_resident(resident, payload):
    return _service.update(resident, payload)
