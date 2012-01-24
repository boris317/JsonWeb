"""
This module provides an api you can use to describe how your classes should be encoded
to json. Here is a quick example::

    import json
    from jsonweb.encode import to_object, JsonWebEncoder
    
    @to_object()
    class DataModel(object):
        def __init__(self, id, value):
            self.id = id
            self.value = value
            
    data = DataModel(5, "foo")
    print json.dumps(data, cls=JsonWebEncoder)
    
The resulting json string would be::

    {"__type__": "DataModel", "id": 5, "value": "foo"}

:func:`to_object` and :func:`to_list` are class decorators. If you have a class you wish to serialize
to a json object decorate it with :func:`to_object`. If your class should serialize into a json list 
decorate it with :func:`to_list`.
"""

import json
import datetime

class EncodeArgs:
    __type__ = None
    serialize_as = None
    handler = None
    suppress = None

def to_object(cls_type=None, suppress=[], handler=None):
    """
    To make your class instances json encodable decorate them with :func:`json_object`. 
    The class instance's ``__dict__`` attribute will be used to retrieve the key/value pairs that will 
    make up the json object (*Minus any attributes that start with an underscore or any attributes 
    that were specified via the* ``suppress`` *keyword agrument*).
    
    Here is an example::
    
        @to_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("Shawn", "Adams")
                                    
    Here is the json encoded ``person`` object::
    
        {"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}    
    
    A ``__type__`` key is automatically added to the json object.  Its value should represent
    the object type being encoded. By default it's set to the value of decorated class's 
    ``__name__`` attribute. You can specify your own value with ``cls_type``::
                        
        @to_object(cls_type="PersonObject")
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("Shawn", "Adams")
                                    
    Encoded as json::
        
        {"__type__": "PersonObject", "first_name": "Shawn", "last_name": "Adams"}
                  
    If you would like to leave certian attributes out of the resultant json object you specify them 
    with the ``suppress`` kw argument::
        
        @to_object(suppress=["guid"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.guid = 12334
                self.first_name = first_name
                self.last_name = last_name
                
    You can even suppress the ``__type__`` attribute::
    
        @to_object(suppress=["guid", "__type__"])
        ...
                          
    If you need more control over how your object is encoded you can specify a ``handler`` callable.
    It should accept one argument, which will be the object to encode, and it should return
    a ``dict``.
    
    Here is an example::
        
        def person_encoder(person):
            return {"FirstName": person.first_name, "LastName": person.last_name}
            
        @to_object(handler=person_encoder)
        class Person(object):
            def __init__(self, first_name, last_name):
                self.guid = 12334
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("Shawn", "Adams")
                
    As you may have guessed, here is the json::
    
        {"FirstName": "Shawn", "LastName": "Adams"}
            
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
    """
    If your class instances should serialize into a json list decorate it with :func:`to_list`. The python built in
    :class:`list` will be called with your class instance as its argument. ie **list(obj)**. This means your class needs to define
    the ``__iter__`` method.
    
    Here is an example::
        
        @json_object(supress=["__type__"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        @json_list
        class People(object):
            def __init__(self, *persons):
                self.persons = persons
                
            def __iter__(self):
                for p in self.persons:
                    yield p
                    
        people = People(
            Person("Luke", "Skywalker"),
            Person("Darth", "Vader"),
            Person("Obi-Wan" "Kenobi")
        )
        
    Encoding``people`` produces this json::
    
        [
            {"first_name": "Luke", last_name: "Skywalker"}, 
            {"first_name": "Darth", last_name: "Vader"}, 
            {"first_name": "Obi-Wan", last_name: "Kenobi"}
        ]
        
    """
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
    Wrapper around :class:`JsonWebEncoder` that allows the passing of keyword
    arguments to it's constructor at a later time. The :func:`json.dumps` keyword argument 
    ``cls`` takes a :class:`type` object(a class) and it is instantiated later. If you 
    wish to pass keyword arguments to the class when it is instantiated you should use this wrapper.
    
    * ``cls`` is a subclass of :class:`JSONEncoder` which defaults to :class:`JsonWebEncoder`.
    
    * ``object_handler`` is the callable responsable for returning a python dict from a :mod:`jsonweb` 
      decorated class instance which defaults to :func:`to_json_object`. 
    
    * Any other ``kw`` arguments will be passed to ``cls`` during instantiation.
    
    Here is an example::
    
        def cammel_case(key):
            return "".join([s.capitalize() for s in key.split("_")])        
        
        def my_object_handler(obj):
            '''cammel case all object keys.'''
            
            json_obj = {}
            for k,v in obj.__dict__.iteritems():
                if not k.startswith("_"):
                    json_obj[cammel_case(k)] = v
            return json_obj
        
        @to_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
        
        person = Person("shawn", "adams")
        json.dumps(person, cls=json_web_encoder(object_handler=my_object_hander))
        
    And the resulting json::
    
        {"FirstName": "shawn", "LastName": "adams"}
    
    """
    cls = cls or JsonWebEncoder
    def factory(*args, **inst_kw):
        inst_kw.update(kw)
        inst_kw["object_handler"] = object_handler
        return cls(*args, **inst_kw)
    return factory

class JsonWebEncoder(json.JSONEncoder):
    """
    This :class:`JSONEncoder` subclass is responsible for encoding instances of 
    classess that have been decorated with :func:`to_object` or :func:`to_list`.
    
    If you want to encode the instances of your decorated classes pass 
    :class:`JsonWebEncoder` as the value for the `cls` keyword agrument to
    :func:json.dumps.
    
    Example::
    
        import json
        json.dumps(obj_instance, cls=JsonWebEncoder)
        
    """
    
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
    
