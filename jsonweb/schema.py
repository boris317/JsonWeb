import inspect
"""

"""
from jsonweb.exceptions import JsonWebError
from jsonweb.decode import _object_handlers

class ValidationError(JsonWebError):
    def __init__(self, message, errors=None):
        JsonWebError.__init__(self, message, "VALIDATION_ERROR")
        self.errors = errors
        
class Validator(object):
    def __init__(self, required=True, nullable=False):
        self.__required = required
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
        return self.validate(item)
        
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
    
class ObjectSchema(Validator):
    __metaclass__ = SchemaMeta

    def validate(self, obj):
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
                    
class List(Validator):
    def __init__(self, validator, **kw):
        Validator.__init__(self, **kw)
        self.validator = validator
        
    def validate(self, item):
        if not isinstance(item, list):
            raise ValidationError("Expected list got %s instead" % self._class_name(item))
        validated_objs = []
        errors = []

        for i, obj in enumerate(item):
            try:
                validated_objs.append(self.validator.validate(obj))
            except ValidationError, e:
                e.error_index = i
                errors.append(e)
        if errors:
            raise ValidationError("Error validating list.", errors=errors)
        return validated_objs

    
"""
Simple Validators
"""
     
class EnsureType(Validator):
    def __init__(self, _type, type_name=None, **kw):
        super(EnsureType, self).__init__(**kw)
        self.__type = _type
        #``_type`` can be a string. This way you can reference a class
        #that may not be defined yet. In this case we must explicity
        #set type_name or an instance is raised inside ``__type_name``
        if isinstance(_type, basestring):
            type_name = _type
        self.__type_name = type_name or self.__type_name(_type)
        
    
    def validate(self, item):
        if not isinstance(item, self.__type):
            raise ValidationError("Expected %s got %s instead." % (self.__type_name, self._class_name(item)))
        return item
    
    def __type_name(self, _type):
        if isinstance(_type, tuple):
            return "(%s)" % ", ".join((t.__name__ for t in _type))
        return _type.__name__
    
    def __get__(self, obj, type=None):

        if type is None:
            return self
        if not isinstance(self.__type, basestring):
            return self
        #``_type`` was a string and now we must get the actual class
        handler = _object_handlers.get(self.__type)

        if not handler:
            raise JsonWebError("Cannot find class %s." % self.__type)
        return EnsureType(handler[1])
        
        
class String(EnsureType):
    def __init__(self, **kw):
        super(String, self).__init__(basestring, type_name="string", **kw)

class Integer(EnsureType):
    def __init__(self, **kw):
        super(Integer, self).__init__(int, **kw)
    
class Float(EnsureType):
    def __init__(self, **kw):
        super(Float, self).__init__(float, **kw)
        
class Number(EnsureType):
    def __init__(self, **kw):
        super(Number, self).__init__((float, int), type_name="number", **kw)
