from jsonweb.schema.base import BaseValidator, ValidationError
from jsonweb.decode import _object_handlers

from jsonweb.exceptions import JsonWebError

class List(BaseValidator):
    def __init__(self, validator, **kw):
        super(List, self).__init__(**kw)
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
     
class EnsureType(BaseValidator):
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