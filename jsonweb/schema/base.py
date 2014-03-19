import inspect
from jsonweb.exceptions import JsonWebError
from jsonweb import encode
from jsonweb.py3k import PY3k, items


def update_dict(d, **kw):
    d.update(kw)
    return d


class _Errors(object):
    def __init__(self, list_or_dict):
        self.errors = list_or_dict

    def add_error(self, exc, key=None, error_type=None, **extras):
        exc = isinstance(exc, ValidationError) and exc or ValidationError(exc)
        if error_type is not None:
            exc.extras["error_type"] = error_type
        exc.extras.update(extras)

        if key is not None:
            self.errors[key] = exc
        else:
            self.errors.append(exc)

    def raise_if_errors(self, reason, **extras):
        if self.errors:
            raise ValidationError(reason, errors=self.errors, **extras)


@encode.to_object()
class ValidationError(JsonWebError):
    def __init__(self, message, errors=None, **extras):
        JsonWebError.__init__(self, message, **extras)
        self.errors = errors
        
    @encode.handler
    def to_json(self):
        obj = {"reason": str(self)}
        obj.update(self.extras)
        if self.errors:
            obj["errors"] = self.errors
        return obj


@encode.to_object()
class BaseValidator(object):
    """
    Abstract base validator which all JsonWeb validators should inherit from.
    """
    def __init__(self, optional=False, nullable=False,
                 default=None, error_type=None):
        """
        :param optional: Is the item optional?
        :param nullable: Can the item's value can be None?
        :param default: A default value for this item.
        :param error_type: An error code that will be displayed when this
                           error is serialized as JSON.
        """
        self.required = (not optional)
        self.nullable = nullable
        self.default = default
        self.error_type = error_type

    def validate(self, item):
        if item is None:
            if self.nullable:
                return item
            raise ValidationError("Cannot be null.")
        return self._validate(item)
    
    @encode.handler
    def to_json(self, **kw):
        obj = {
            "required": self.required,
            "nullable": self.nullable
        }
        obj.update(kw)
        return obj
    
    def _validate(self, item):        
        raise NotImplemented

    def raise_error(self, message, *args):
        if len(args):
            message = message.format(*args)

        exc = ValidationError(message)

        if self.error_type is not None:
            exc.extras["error_type"] = self.error_type
        raise exc


class SchemaMeta(type):
    def __new__(mcs, class_name, bases, class_dict):
        fields = []
        for k, v in items(class_dict):
            if hasattr(v, "_validate"):
                fields.append(k)
        class_dict["_fields"] = fields
        return type.__new__(mcs, class_name, bases, class_dict)


class ObjectSchema(BaseValidator):
    __metaclass__ = SchemaMeta

    def to_json(self):
        return super(ObjectSchema, self).to_json(
            fields=dict([(f, getattr(self, f)) for f in self._fields])
        )
    
    def _validate(self, obj):
        isinstance_or_raise(obj, dict)
        val_obj = {}
        errors = _Errors({})

        for field in self._fields:
            v = getattr(self, field)
            try:
                if field not in obj:
                    if v.default is not None:
                        val_obj[field] = v.default
                    elif v.required:
                        errors.add_error("Missing required parameter.",
                                         key=field, error_type="required_but_missing")
                else:
                    val_obj[field] = v.validate(obj[field])
            except ValidationError as e:
                errors.add_error(e, key=field)

        errors.raise_if_errors("Error validating object.",
                               error_type="invalid_object")
        return val_obj


def bind_schema(type_name, schema_obj):
    """
    Use this function to add an :class:`ObjectSchema` to a class already
    decorated by :func:`from_object`.
    """
    from jsonweb.decode import _default_object_handlers
    _default_object_handlers._update_handler_deferred(type_name, 
                                                      schema=schema_obj)


def isinstance_or_raise(obj, cls):
    if not isinstance(obj, cls):
        raise ValidationError("Expected {0} got {1} instead.".format(
            cls_name(cls),
            cls_name(obj)
        ), error_type="invalid_type")


def cls_name(obj):
    if inspect.isclass(obj):
        return obj.__name__
    return obj.__class__.__name__


if PY3k:
    ObjectSchema = SchemaMeta(
        ObjectSchema.__name__,
        (BaseValidator, ),
        dict(vars(ObjectSchema))
    )