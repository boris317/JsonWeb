from jsonweb.exceptions import JsonWebError
from jsonweb import encode
from jsonweb.py3k import PY3k, items


def update_dict(d, **kw):
    d.update(kw)
    return d


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
    def __init__(self, optional=False, nullable=False, default=None):
        """
        :param optional: Is the item optional?
        :param nullable: Can the item's value can be None?
        :param default: A default value for this item.
        """
        self.required = (not optional)
        self.nullable = nullable
        self.default = default

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
    
    def _class_name(self, obj):
        return obj.__class__.__name__
    

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
        val_obj = {}
        errors = {}

        if not isinstance(obj, dict):
            raise ValidationError(
                "Expected dict got {0} instead.".format(self._class_name(obj))
            )

        for field in self._fields:
            v = getattr(self, field)

            try:
                if field not in obj:
                    if v.default is not None:
                        val_obj[field] = v.default
                    elif v.required:
                        errors[field] = ValidationError("Missing required parameter.")
                else:
                    val_obj[field] = v.validate(obj[field])
            except ValidationError as e:
                    errors[field] = e
        if errors:
            raise ValidationError("Error validating object.", errors)
        return val_obj


def bind_schema(type_name, schema_obj):
    """
    Use this function to add an :class:`ObjectSchema` to a class already
    decorated by :func:`from_object`.
    """
    from jsonweb.decode import _default_object_handlers
    _default_object_handlers._update_handler_deferred(type_name, 
                                                      schema=schema_obj)


if PY3k:
    ObjectSchema = SchemaMeta(
        ObjectSchema.__name__,
        (BaseValidator, ),
        dict(vars(ObjectSchema))
    )