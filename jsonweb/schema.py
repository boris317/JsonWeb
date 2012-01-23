
class ValidationError(Exception):
    def __init__(self, message, errors=None):
        Exception.__init__(self, message)
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

class SchemaMeta(type):
    def __new__(meta, class_name, bases, class_dict):
        fields = {}
        for k,v in class_dict.iteritems():
            if hasattr(v, "_validate"):
                fields[k] = v
        class_dict["_fields"] = fields
        return type.__new__(meta, class_name, bases, class_dict)    
    
class ObjectSchema(Validator):
    __metaclass__ = SchemaMeta

    def validate(self, obj):
        val_obj = {}
        errors = {}        
        if not isinstance(obj, dict):
            raise ValidationError("Expected dict got %s instead" % (self._type_name(obj)))
        for k, v in self._fields.iteritems():
            try:
                val_obj[k] = v.validate(obj[k])
            except KeyError, e:
                if v.is_required():
                    errors[k] = ValidationError("Missing required parameter.")
            except ValidationError, e:
                    errors[k] = e
        if errors:
            raise ValidationError("", errors)
        return val_obj
    
    def _prop_str(self, k=None):
        cls = self.__class__.__name__
        if k:
            return "%s.%s" % (cls, k)
        return cls 
                
class ListSchema(Validator):
    def __init__(self, validator, **kw):
        Validator.__init__(self, **kw)
        self.validator = validator
        
    def validate(self, item):
        if not isinstance(item, list):
            raise ValidationError("Expected list got %s instead" % self._type_name(item))
        try:
            return [self.validator.to_obj(obj) for i, obj in enumerate(item)]
        except ValidationError, e:
            e.obj_index = i
            raise e
            
class EnsureType(Validator):
    def __init__(self, _type):
        self._type
    def validate(self, item):
        if not isinstance(item, _type):
            raise ValidationError("Expected %s got %s instead." % (self.cls.__name__, self._type_name(item)))
        
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
   