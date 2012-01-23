import json
import datetime

"""
``to_object`` and ``to_list`` are class decorators. If you have a class you wish to serialize
to a json object decorate it with @json_object. The class instances __dict__ attr will be used to
retrieve the key/value pairs that will make up the json object. Minus any attributes that start
with and underscore or any attributes that were specified via the ``suppress`` keyword.

If your class should serialize into a json list decorate it with @to_list. "list" will be
called with your class as its argument. ie list(cls). This means your class needs to define
the __iter__ method.

"""

class EncodeArgs:
    __type__ = None
    serialize_as = None
    handler = None
    suppress = None

def to_object(cls_type=None, handler=None, suppress=[]):
    """
    ``cls_type`` will be added to your class as __type__. This way all of your json responses
    will include the __type__ key for your objects. If __type__ is None it will be infered from
    cls.__name__
    
    ``handler`` lets you specify a callable that will return the a python dict ready to encode
    to json. Use a ``handler`` if you want greater control over how your object is encoded
    to json. The callable should except one agrument that is an instance of the decorated class.
    
    Here is an example:
        
    def person_encoder(person):
        return {"FirstName": person.first_name, "LastName": person.last_name}
    
    @to_object(handler=person_encoder)
    class Person(object):
        def __init__(self, first_name, last_name):
            self.guid = 12334
            self.first_name = first_name
            self.last_name = last_name
            
    If you would like to leave certian attributes out of the resultant json object you 
    specify them with the ``suppress`` kw argument.
    
    @to_object(suppress=["guid"])
    class Person(object):
        def __init__(self, first_name, last_name):
            self.guid = 12334
            self.first_name = first_name
            self.last_name = last_name
                
    Person instances will serialize into json objects that do not include the "guid" attr. 
    ie: {"name": "Shawn", "last_name": "Adams"}
    """
    def wrapper(cls):
        cls._encode = EncodeArgs()
        cls._encode.serialize_as = "json_object"
        cls._encode.handler = handler
        cls._encode.suppress = suppress
        cls._encode.__type__ = cls_type or cls.__name__        
        return cls
    
    return wrapper
    
def to_list(cls):
    cls._serialize_as = "json_list"
    return cls

def to_json_object(obj):
    suppress = obj._encode.suppress
    json_obj = dict([(k,v) for k,v in obj.__dict__.iteritems() if not k.startswith("_") and k not in suppress])
    if "__type__" not in suppress:
        json_obj["__type__"] = obj._encode.__type__
    return json_obj

def json_web_encoder(cls=None, object_handler=None, **kw):
    """
    Wrapper around JsonWebEncoder that allows the passing of keyword
    arguments to it's constructor at a later time. 
    
    json.dumps' keyword argument ``cls`` takes a type object(ie class) 
    and it is institiated later. If you wish to pass keyword arguments to
    the class when it is instantiated must use this wrapper.
    
    example:
    json.dumps(obj, cls=json_web_encoder(object_handler=my_object_hander))    
    
    """
    cls = cls or JsonWebEncoder
    def factory(*args, **inst_kw):
        inst_kw.update(kw)
        inst_kw["object_handler"] = object_handler
        return cls(*args, **inst_kw)
    return factory

class JsonWebEncoder(json.JSONEncoder):
    _DT_FORMAT = "%Y-%m-%dT%H:%M:%S"
    def __init__(self, *args, **kw):
        self.object_handler = kw.pop("object_handler", None) or to_json_object        
        json.JSONEncoder.__init__(self, *args, **kw)
        
    def default(self, o):
        
        try:
            e_args = getattr(o, "_encode")
        except AttributeError:
            pass
        else:
            if e_args.serialize_as == "json_object":
                if e_args.handler:
                    return e_args.handler(o)
                return self.object_handler(o)
            elif e_args.serialize_as == "json_list":
                return list(o)
            
        if isinstance(o, datetime):
            return o.strftime(self._DT_FORMAT)            
        return json.JSONEncoder.default(self, o)
    
