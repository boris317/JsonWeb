from jsonweb.exceptions import JsonWebError
from jsonweb import encode
from jsonweb.py3k import PY3k, items


def update_dict(d, **kw):
    d.update(kw)
    return d


@encode.to_object()
class ValidationError(JsonWebError):
    def __init__(self, message, errors=None):
        JsonWebError.__init__(self, message)
        self.errors = errors
        
    @encode.handler
    def to_json(self):
        if self.errors:
            return {"message": self.message, "errors": self.errors}
        return self.message


@encode.to_object()
class BaseValidator(object):
    def __init__(self, optional=False, nullable=False):
        self.__required = (not optional)
        self.__nullable = nullable
        
    def is_required(self):
        return self.__required

    def is_nullable(self):
        return self.__nullable
    
    def validate(self, item):
        if item is None:
            if self.is_nullable():
                return item
            raise ValidationError("Cannot be null.")
        return self._validate(item)
    
    @encode.handler
    def to_json(self, **kw):
        obj = {
            "required": self.is_required(),
            "nullable": self.is_nullable()
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
                val_obj[field] = v.validate(obj[field])
            except KeyError:
                if v.is_required():
                    errors[field] = ValidationError("Missing required parameter.")
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