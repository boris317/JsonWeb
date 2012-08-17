from jsonweb.exceptions import JsonWebError
from jsonweb import encode

@encode.to_object()
class ValidationError(JsonWebError):
    def __init__(self, message, errors=None):
        JsonWebError.__init__(self, message, "VALIDATION_ERROR")
        self.errors = errors
    @encode.handler
    def to_json(self):
        error = {"message": self.message}
        if self.errors:
            error["errors"] = self.errors
        return error
            
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
        
    def _validate(self, item):        
        raise NotImplemented
    
    def _class_name(self, obj):
        return obj.__class__.__name__
    
"""
Complex validators
"""

class SchemaMeta(type):
    def __new__(meta, class_name, bases, class_dict):
        fields = []
        for k,v in class_dict.iteritems():
            if hasattr(v, "_validate"):
                fields.append(k)
        class_dict["_fields"] = fields
        return type.__new__(meta, class_name, bases, class_dict)    
    
class ObjectSchema(BaseValidator):
    __metaclass__ = SchemaMeta

    def _validate(self, obj):
        val_obj = {}
        errors = {}        
        if not isinstance(obj, dict):
            raise ValidationError("Expected dict got %s instead" % (self._class_name(obj)))
        for field in self._fields:
            v = getattr(self, field)
            try:
                val_obj[field] = v.validate(obj[field])
            except KeyError, e:
                if v.is_required():
                    errors[field] = ValidationError("Missing required parameter.")
            except ValidationError, e:
                    errors[field] = e
        if errors:
            raise ValidationError("Error validating object", errors)
        return val_obj
    
def bind_schema(type_name, schema_obj):
    from jsonweb.decode import _default_object_handlers
    """
    Use this function to add an :class:`ObjectSchema` to a class already
    decorated by :func:`from_object`.
    """
    _default_object_handlers._update_handler_deferred(type_name, schema=schema_obj)