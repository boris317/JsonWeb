"""
Validators for use in :mod:`jsonweb.schema`. 
"""
from datetime import datetime

from jsonweb.decode import _default_object_handlers
from jsonweb.exceptions import JsonWebError
from jsonweb.schema.base import BaseValidator, ValidationError

class List(BaseValidator):
    """
    Validates a list of things. The List constructor accepts
    a validator and each item in a the list will be validated
    against it ::
    
        >>> List(Integer).validate([1,2,3,4])
        ... [1,2,3,4]
    
        >>> List(Integer).validate(10)
        ...
        ValidationError: Expected list got int instead.
        
    Since :class:`ObjectSchema` is also a validator we can do this ::
    
        >>> class PersonSchema(ObjectSchema):
        ...     first_name = String()
        ...     last_name = String()
        ...
        >>> List(PersonSchema).validate([
        ...     {"first_name": "bob", "last_name": "smith"},
        ...     {"first_name": "jane", "last_name": "smith"}
        ... ])
        
    """
    def __init__(self, validator, **kw):
        super(List, self).__init__(**kw)
        if type(validator) is type:
            self.validator = validator()
        else:
            self.validator = validator
        
    def validate(self, item):
        if not isinstance(item, list):
            raise ValidationError("Expected list got %s instead." % self._class_name(item))
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
    """
    Validates something is a certian type ::
    
        >>> class Person(object):
        ...     pass
        >>> EnsureType(Person).validate(Person())
        ... <Person>
        >>> EnsureType(Person).validate(10)
        Traceback (most recent call last):
            ...
        ValidationError: Expected Person got int instead.        
        
    """
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
            return "one of (%s)" % ", ".join((t.__name__ for t in _type))
        return _type.__name__
    
    def __get__(self, obj, type=None):

        if type is None:
            return self
        if not isinstance(self.__type, basestring):
            return self
        #``_type`` was a string and now we must get the actual class
        handler = _default_object_handlers.get(self.__type)

        if not handler:
            raise JsonWebError("Cannot find class %s." % self.__type)
        return EnsureType(handler[1])
        
        
class String(EnsureType):
    """
    Validates something is a string ::
    
        >>> String().validate("foo")
        ... 'foo'
        >>> String().validate(1)
        Traceback (most recent call last):
            ...
        ValidationError: Expected str got int instead.
        
    """
    def __init__(self, **kw):
        super(String, self).__init__(basestring, type_name="str", **kw)

class Integer(EnsureType):
    """ Validates something in an integer """
    def __init__(self, **kw):
        super(Integer, self).__init__(int, **kw)
    
class Float(EnsureType):
    """ Validates something is a float """
    def __init__(self, **kw):
        super(Float, self).__init__(float, **kw)
        
class Number(EnsureType):
    """
    Validates something is a number ::
    
        >>> Number().validate(1)
        ... 1
        >>> Number().validate(1.1)
        >>> 1.1
        >>> Number().validate("foo")
        Traceback (most recent call last):
            ...
        ValidationError: Expected number got int instead.
        
    """
    def __init__(self, **kw):
        super(Number, self).__init__((float, int), type_name="number", **kw)

class DateTime(BaseValidator):
    """
    Validates that something is a date/datetime string ::
    
        >>> DateTime().validate("2010-01-02 12:30:00")
        ... datetime.datetime(2010, 1, 2, 12, 30)
        
        >>> DateTime().validate("2010-01-02 12:300")
        Traceback (most recent call last):
            ...
        ValidationError: time data '2010-01-02 12:300' does not match format '%Y-%m-%d %H:%M:%S'
        
    The default datetime format is ``%Y-%m-%d %H:%M:%S``. You can specify your own ::
    
        >>> DateTime("%m/%d/%Y").validate("01/02/2010")
        ... datetime.datetime(2010, 1, 2, 0, 0)    
        
        
    """
    def __init__(self, format="", **kw):
        super(DateTime, self).__init__(**kw)
        self.format = format or "%Y-%m-%d %H:%M:%S"
        
    def validate(self, item):
        try:
            return datetime.strptime(item, self.format)
        except ValueError, e:
            raise ValidationError(str(e))
    