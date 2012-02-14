"""
Often times in a web application the data you wish to return to users is described by some sort
of data model or resource in the form of a class object. This module provides an easy way to encode
your python class instances to json Here is a quick example::

    >>> import json
    >>> from jsonweb.encode import to_object, JsonWebEncoder
    
    >>> @to_object()
    ... class DataModel(object):
    ...      def __init__(self, id, value):
    ...          self.id = id
    ...          self.value = value
            
    >>> data = DataModel(5, "foo")
    >>> json.dumps(data, cls=JsonWebEncoder)
    '{"__type__": "DataModel", "id": 5, "value": "foo"}'

:func:`to_object` and :func:`to_list` are class decorators. If you have a class you wish to serialize
to a json object decorate it with :func:`to_object`. If your class should serialize into a json list 
decorate it with :func:`to_list`.

.. note::

    Remember to pass :class:`JsonWebEncoder` as the ``cls`` argument to :func:`json.dumps`.
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
    
        >>> @to_object()
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
                
        >>> person = Person("Shawn", "Adams")
        >>> json.dumps(person, cls=JsonWebEncoder)                                        
        '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}'
    
    A ``__type__`` key is automatically added to the json object.  Its value should represent
    the object type being encoded. By default it is set to the value of the decorated class's 
    ``__name__`` attribute. You can specify your own value with ``cls_type``::
                        
        >>> @to_object(cls_type="PersonObject")
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
                
        >>> person = Person("Shawn", "Adams")
        >>> json.dumps(person, cls=JsonWebEncoder)        
        '{"__type__": "PersonObject", "first_name": "Shawn", "last_name": "Adams"}'
                  
    If you would like to leave some attributes out of the resulting json simply
    use the ``suppress`` kw argument to pass a list of attribute names::
           
        >>> @to_object(suppress=["last_name"])
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
        
        >>> person = Person("Shawn", "Adams")
        >>> json.dumps(person, cls=JsonWebEncoder)
        '{"__type__": "Person", "first_name": "Shawn"}'        
                
    You can even suppress the ``__type__`` attribute ::
    
        @to_object(suppress=["last_name", "__type__"])
        ...
                          
    If you need greater control over how your object is encoded you can specify a ``handler`` callable.
    It should accept one argument, which is the object to encode, and it should return
    a dict. This would overide the default object handler :func:`JsonWebEncoder.object_handler`.
    
    Here is an example::
        
        >>> def person_encoder(person):
        ...     return {"FirstName": person.first_name, "LastName": person.last_name}
            
        >>> @to_object(handler=person_encoder)
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.guid = 12334
        ...         self.first_name = first_name
        ...         self.last_name = last_name
                
        >>> person = Person("Shawn", "Adams")
        >>> json.dumps(person, cls=JsonWebEncoder)        
        '{"FirstName": "Shawn", "LastName": "Adams"}'
            
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
        
    Encoding ``people`` produces this json::
    
        [
            {"first_name": "Luke", last_name: "Skywalker"}, 
            {"first_name": "Darth", last_name: "Vader"}, 
            {"first_name": "Obi-Wan", last_name: "Kenobi"}
        ]
        
    """
    cls._serialize_as = "json_list"
    return cls


class JsonWebEncoder(json.JSONEncoder):
    """
    This :class:`json.JSONEncoder` subclass is responsible for encoding instances of 
    classess that have been decorated with :func:`to_object` or :func:`to_list`. Pass 
    :class:`JsonWebEncoder` as the value for the ``cls`` keyword agrument to
    :func:`json.dump` or :func:`json.dumps`.
    
    Example::
    
        json.dumps(obj_instance, cls=JsonWebEncoder)
            
    """
    
    _DT_FORMAT = "%Y-%m-%dT%H:%M:%S"
        
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
                return self.list_handler(o)
            
        if isinstance(o, datetime):
            return o.strftime(self._DT_FORMAT)            
        return json.JSONEncoder.default(self, o)
    
    def object_handler(self, obj):
        """
        Handles encoding instance objects of classes decorated by :func:`to_object`. Returns
        a dict containing all the key/value pairs in ``obj.__dict__``. Excluding attributes that 
        
        * start with an underscore.
        * were specified with the ``suppress`` keyword agrument of :func:`to_object`.
        
        The returned dict will be encoded into json.
        
        .. note::
        
            Override this method if you wish to change how ALL objects are encoded into json objects.
            
        """        
        suppress = obj._encode.suppress
        json_obj = dict([(k,v) for k,v in obj.__dict__.iteritems() if not k.startswith("_") and k not in suppress])
        if "__type__" not in suppress:
            json_obj["__type__"] = obj._encode.__type__
        return json_obj
    
        
    def list_handler(self, obj):
        """
        Handles encoding instance objects of classes decorated by :func:`to_list`. Simply calls
        :class:`list` on ``obj``. Classes decorated by :func:`to_list` should define an ``__iter__``
        method.
        
        .. note::
        
            Override this method if you wish to change how ALL objects are encoded into json lists.        
        
        
        """
        
        return list(obj)