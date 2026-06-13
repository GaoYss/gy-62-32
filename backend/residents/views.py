from django.core.exceptions import ValidationError
from django.db import IntegrityError

from backend.common.crud import make_collection_view, make_detail_view

from .services import ResidentCRUDService


_resident_exceptions = (ValidationError, IntegrityError, TypeError, ValueError)

residents_collection = make_collection_view(
    ResidentCRUDService,
    create_exceptions=_resident_exceptions,
)

resident_detail = make_detail_view(
    ResidentCRUDService,
    update_exceptions=_resident_exceptions,
)
