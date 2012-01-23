import json
from datetime import datetime

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class JsonDecodeError(Exception):
    """
    Raised for mailformed json.
    """
    def __init__(self, message):
        Exception.__init__(self, message, "JSON_PARSE_ERROR")
        
class ObjectDecodeError(Exception):
    """
    Raisded when python containers (dicts and lists) cannot be decoded into
    complex types. These exceptions are raised from within an ObjectHook instance.
    """
    def __init__(self, message, **extras):
        Exception.__init__(self, message, "DATA_DECODE_ERROR")

class ObjectMissingAttributeError(ObjectDecodeError):
    def __init__(self, obj, attr):
        ObjectDecodeError.__init__(self, 
            "Missing %s attribute for %s." % (attr, obj), 
            sub_type="MISSING_ATTRIBUTE",
            obj=obj, 
            attr=attr
        )

class ObjectNotFoundError(ObjectDecodeError):
    def __init__(self, obj):
        ObjectDecodeError.__init__(self, 
            "Cannot decode object %s. No such object." % obj, 
            sub_error="OBJECT_NOT_FOUND",
            obj=obj,
        )

def json_request(func):
    """
    Decorate pyramid view callables that require a decoded json request.  If the request
    content_type is application/json it will attempt to decode the string in request.body
    as JSON. The python data structure will be set on the request obj as "decoded_obj"
    Raises BadRequestError otherwise.
    """
    def wrapper(request):
        if not request.content_type == "application/json":
            raise BadRequestError("Missing JSON data")
        
        try:
            obj = json.load(request.body_file, object_hook=object_hook)
        except ValueError, e:
            raise JsonDecodeError(e.args[0])
        request.decoded_obj = obj
        
        return func(request)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


class ObjectHook(object):
    """
    Class responsible for decoding json objects to python classes. 
    """
    _DT_FORMAT = _DATETIME_FORMAT
            
    def __init__(self):
        self.handlers = {}        
            
    def decode_obj(self, obj):
        """        
        This method is called for every json obj decoded in a json string. The presense
        of the key __type__ in obj will trigger a lookup in self.factories. If a factory is
        not found for __type__ then an ObjectNotFoundError is raised. If a factory is found it will
        be called with "obj" as it only argument. If all goes well it should return a new
        python instant of type __type__.        
        """
        if "__type__" not in obj:
            return obj
        
        obj_type = obj["__type__"]
        try:
            factory, cls, schema = self.handlers[obj_type]
        except KeyError:
            raise ObjectNotFoundError(obj_type)
        
        try:
            if schema:
                return factory(cls, schema().to_obj(obj))
            else:
                return factory(cls, obj)
        except KeyError, e:
            raise ObjectMissingAttributeError(obj_type, e.args[0])
        
    def _datetime(self, dt):
        if dt is None:
            return
        try:
            return datetime.strptime(dt, self._DT_FORMAT)
        except TypeError, e:
            raise ObjectDecodeError("datetime attribute for %s must be a string, not %s" % (self.obj, type(dt)))
        except ValueError, e:
            raise ObjectDecodeError(e.args[0])
        
    def add_handler(self, cls, handler, type_name=None, schema=None):
        self.handlers[type_name or cls.__name__] = (handler, cls, schema)

decode = ObjectHook()

#import from_object and decorate your classes with it.
def from_object(handler, type_name=None, schema=None):
    def wrapper(cls):
        decode.add_handler(cls, handler, type_name, schema)
        return cls
    return wrapper

def object_hook(obj):
    """
    object_hook callable used when decoding json requests into python objects.
    """
    return decode.decode_obj(obj)
