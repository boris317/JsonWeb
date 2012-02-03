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
    def _type_name(self, obj):
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
            raise ValidationError("Expected dict got %s instead" % (self._type_name(obj)))
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
    
    def _prop_str(self, k=None):
        cls = self.__class__.__name__
        if k:
            return "%s.%s" % (cls, k)
        return cls 
                
class List(Validator):
    def __init__(self, validator, **kw):
        Validator.__init__(self, **kw)
        self.validator = validator
        
    def validate(self, item):
        if not isinstance(item, list):
            raise ValidationError("Expected list got %s instead" % self._type_name(item))
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
    def __init__(self, _type):
        self._type = _type
        
    def validate(self, item):
        if not isinstance(item, self._type):
            raise ValidationError("Expected %s got %s instead." % (self._type.__name__, self._type_name(item)))
        return item
        
    def __get__(self, obj, type=None):

        if type is None:
            return self
        if not isinstance(self._type, basestring):
            return self
        #``_type`` can be a string. This way you can reference a class
        #that may not be defined yet. But now we have to get the class
        handler = _object_handlers.get(self._type)
        print handler
        if not handler:
            raise JsonWebError("Cannot find class %s." % self._type)
        return EnsureType(handler[1])
        
        
class String(Validator):
    def validate(self, item):
        if not isinstance(item, basestring):
            raise ValidationError("Expected string got %s instead." % self._type_name(item))
        return item

class Integer(Validator):
    def validate(self, item):
        if not isinstance(item, int):
            raise ValidationError("Expected int got %s instead." % self._type_name(item))
        return item         
    
class Float(Validator):
    def validate(self, item):
        try:
            return float(item)
        except (TypeError, ValueError):
            raise ValidationError("Expected float got %s instead." % self._type_name(item))        
   