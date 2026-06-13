from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError

from backend.common.crud import make_collection_view, make_detail_view

from .services import VisitCRUDService


_visit_exceptions = (ObjectDoesNotExist, ValidationError, IntegrityError, KeyError, TypeError, ValueError)
_visit_update_exceptions = (ObjectDoesNotExist, ValidationError, IntegrityError, TypeError, ValueError)

visits_collection = make_collection_view(
    VisitCRUDService,
    create_exceptions=_visit_exceptions,
)

visit_detail = make_detail_view(
    VisitCRUDService,
    update_exceptions=_visit_update_exceptions,
)
