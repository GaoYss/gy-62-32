from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .http import error, list_response, ok, parse_json


DEFAULT_CREATE_EXCEPTIONS = (
    ObjectDoesNotExist,
    ValidationError,
    IntegrityError,
    KeyError,
    TypeError,
    ValueError,
)


class BaseCRUDService:
    model = None
    write_fields = None
    serialize_fields = None
    exclude_on_create = None
    exclude_on_update = None
    select_related = None
    datetime_fields = None
    relation_fields = None
    field_serializers = None

    def __init__(self):
        if self.write_fields is None:
            raise NotImplementedError("subclasses must define write_fields")
        if self.model is None:
            raise NotImplementedError("subclasses must define model")
        if self.serialize_fields is None:
            self.serialize_fields = []
        if self.exclude_on_create is None:
            self.exclude_on_create = {"id"}
        if self.exclude_on_update is None:
            self.exclude_on_update = {"id"}
        if self.datetime_fields is None:
            self.datetime_fields = []
        if self.relation_fields is None:
            self.relation_fields = {}
        if self.field_serializers is None:
            self.field_serializers = {}

    # ---- queryset hooks ----

    def get_queryset(self):
        qs = self.model.objects.all()
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        return qs

    def get_detail_queryset(self):
        return self.get_queryset()

    def filter_queryset(self, queryset, params):
        return queryset

    # ---- payload hooks ----

    def normalize_payload(self, payload):
        return {field: payload.get(field) for field in self.write_fields if field in payload}

    def validate_related(self, data):
        pass

    # ---- serialization ----

    def serialize(self, instance):
        result = {}
        for field in self.serialize_fields:
            result[field] = self._serialize_field_value(instance, field)
        return result

    def _serialize_field_value(self, instance, field):
        if field in self.field_serializers:
            return self.field_serializers[field](instance)
        if field in self.relation_fields:
            rel_info = self.relation_fields[field]
            rel_instance = getattr(instance, field, None)
            if rel_instance is not None:
                return rel_info["serializer"](rel_instance)
            return None
        if field.endswith("_id") and field[:-3] in self.relation_fields:
            return getattr(instance, field, None)
        return self.serialize_field_default(instance, field)

    def serialize_field_default(self, instance, field):
        value = getattr(instance, field, None)
        if value is None:
            return None
        if field in self.datetime_fields or (hasattr(value, "isoformat") and not isinstance(value, str)):
            return value.isoformat()
        return value

    def serialize_list(self, items):
        return [self.serialize(item) for item in items]

    # ---- crud operations ----

    def list(self, params=None):
        qs = self.get_queryset()
        qs = self.filter_queryset(qs, params or {})
        return self.serialize_list(qs)

    def build_instance(self, payload):
        data = self.normalize_payload(payload)
        data = {k: v for k, v in data.items() if k not in self.exclude_on_create}
        self.validate_related(data)
        return self.model(**data)

    def create(self, payload):
        instance = self.build_instance(payload)
        instance.full_clean()
        instance.save()
        self.after_create(instance, payload)
        return instance

    def update(self, instance, payload):
        data = self.normalize_payload(payload)
        for field, value in data.items():
            if field not in self.exclude_on_update:
                setattr(instance, field, value)
        self.validate_related(data)
        instance.full_clean()
        instance.save()
        self.after_update(instance, payload)
        return instance

    def after_create(self, instance, payload):
        pass

    def after_update(self, instance, payload):
        pass


def make_collection_view(service_cls, create_exceptions=None, list_params_extractor=None):
    service = service_cls()
    if create_exceptions is None:
        create_exceptions = DEFAULT_CREATE_EXCEPTIONS

    @csrf_exempt
    @require_http_methods(["GET", "POST", "OPTIONS"])
    def view(request):
        if request.method == "GET":
            params = list_params_extractor(request) if list_params_extractor else request.GET
            return list_response(service.list(params))

        try:
            instance = service.create(parse_json(request))
            return ok(service.serialize(instance), status=201)
        except create_exceptions as exc:
            return error(str(exc))

    return view


def make_detail_view(service_cls, update_exceptions=None):
    service = service_cls()
    if update_exceptions is None:
        update_exceptions = DEFAULT_CREATE_EXCEPTIONS

    @csrf_exempt
    @require_http_methods(["GET", "PUT", "DELETE", "OPTIONS"])
    def view(request, pk):
        instance = get_object_or_404(service.get_detail_queryset(), pk=pk)

        if request.method == "GET":
            return ok(service.serialize(instance))

        if request.method == "DELETE":
            instance.delete()
            return ok({"deleted": True})

        try:
            instance = service.update(instance, parse_json(request))
            return ok(service.serialize(instance))
        except update_exceptions as exc:
            return error(str(exc))

    return view
