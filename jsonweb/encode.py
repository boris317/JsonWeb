"""
Often times in a web application the data you wish to return to users is
described by some sort of data model or resource in the form of a class
object. This module provides an easy way to encode your python class
instances to JSON. Here is a quick example::
 
    >>> from jsonweb.encode import to_object, dumper
    >>> @to_object()
    ... class DataModel(object):
    ...      def __init__(self, id, value):
    ...          self.id = id
    ...          self.value = value
            
    >>> data = DataModel(5, "foo")
    >>> dumper(data)
    '{"__type__": "DataModel", "id": 5, "value": "foo"}'

If you have a class you wish to serialize to a JSON object decorate it with
:func:`to_object`. If your class should serialize into a JSON list decorate
it with :func:`to_list`.
"""

import json
import datetime
import types


class EncodeArgs:
    __type__ = None
    serialize_as = None
    handler = None
    suppress = None


def handler(func):
    """
    Use this decorator to mark a method on a class as being its jsonweb
    encode handler. It will be called any time your class is serialized to a
    JSON string. ::

        >>> from jsonweb import encode           
        >>> @encode.to_object()
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
        ...     @encode.handler
        ...     def to_obj(self):
        ...         return {"FirstName": person.first_name, 
        ...             "LastName": person.last_name}
        ...
        >>> @encode.to_list()
        ... class People(object):
        ...     def __init__(self, *persons):
        ...         self.persons = persons        
        ...     @encode.handler
        ...     def to_list(self):
        ...         return self.persons
        ...
        >>> people = People(
        ...     Person("Luke", "Skywalker"),
        ...     Person("Darth", "Vader"),
        ...     Person("Obi-Wan" "Kenobi")
        ... )
        ...
        >>> print dumper(people, indent=2)
        [
          {
            "FirstName": "Luke", 
            "LastName": "Skywalker"
          }, 
          {
            "FirstName": "Darth", 
            "LastName": "Vader"
          }, 
          {
            "FirstName": "Obi-Wan", 
            "LastName": "Kenobi"
          }
        ]

    """
    func._jsonweb_encode_handler = True
    return func


def __inspect_for_handler(cls):
    cls._encode.handler_is_instance_method = False
    if cls._encode.handler:
        return cls
    for attr in dir(cls):
        if attr.startswith("_"):
            continue
        obj = getattr(cls, attr)
        if hasattr(obj, "_jsonweb_encode_handler"):
            cls._encode.handler_is_instance_method = True
            # we store the handler as a string name here. This is 
            # because obj is an unbound method. When its time to
            # encode the class instance we want to call the bound
            # instance method.
            cls._encode.handler = attr
            break
    return cls


def to_object(cls_type=None, suppress=None, handler=None, exclude_nulls=False):
    """
    To make your class instances JSON encodable decorate them with
    :func:`to_object`. The python built-in :py:func:`dir` is called on the
    class instance to retrieve key/value pairs that will make up the JSON
    object (*Minus any attributes that start with an underscore or any
    attributes that were specified via the* ``suppress`` *keyword argument*).
    
    Here is an example::

        >>> from jsonweb import to_object
        >>> @to_object()
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
                
        >>> person = Person("Shawn", "Adams")
        >>> dumper(person)
        '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}'
    
    A ``__type__`` key is automatically added to the JSON object. Its value
    should represent the object type being encoded. By default it is set to
    the value of the decorated class's ``__name__`` attribute. You can
    specify your own value with ``cls_type``::

        >>> from jsonweb import to_object
        >>> @to_object(cls_type="PersonObject")
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
                
        >>> person = Person("Shawn", "Adams")
        >>> dumper(person)
        '{"__type__": "PersonObject", "first_name": "Shawn", "last_name": "Adams"}'
                  
    If you would like to leave some attributes out of the resulting JSON
    simply use the ``suppress`` kw argument to pass a list of attribute
    names::

        >>> from jsonweb import to_object
        >>> @to_object(suppress=["last_name"])
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
        
        >>> person = Person("Shawn", "Adams")
        >>> dumper(person)
        '{"__type__": "Person", "first_name": "Shawn"}'        
                
    You can even suppress the ``__type__`` attribute ::
    
        @to_object(suppress=["last_name", "__type__"])
        ...
        
    Sometimes it's useful to suppress ``None`` values from your JSON output.
    Setting ``exclude_nulls`` to ``True`` will accomplish this ::

        >>> from jsonweb import to_object
        >>> @to_object(exclude_nulls=True)
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
    
        >>> person = Person("Shawn", None)
        >>> dumper(person)
        '{"__type__": "Person", "first_name": "Shawn"}'
    
    .. note:: 
    
        You can also pass most of these arguments to :func:`dumper`. They
        will take precedence over what you passed to :func:`to_object` and
        only effects that one call.
    
    If you need greater control over how your object is encoded you can
    specify a ``handler`` callable. It should accept one argument, which is
    the object to encode, and it should return a dict. This would override the
    default object handler :func:`JsonWebEncoder.object_handler`.
    
    Here is an example::

        >>> from jsonweb import to_object
        >>> def person_encoder(person):
        ...     return {"FirstName": person.first_name, 
        ...         "LastName": person.last_name}
        ...
        >>> @to_object(handler=person_encoder)
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.guid = 12334
        ...         self.first_name = first_name
        ...         self.last_name = last_name
                
        >>> person = Person("Shawn", "Adams")
        >>> dumper(person)
        '{"FirstName": "Shawn", "LastName": "Adams"}'
        
        
    You can also use the alternate decorator syntax to accomplish this. See
    :func:`jsonweb.encode.handler`.
            
    """
    def wrapper(cls):
        cls._encode = EncodeArgs()
        cls._encode.serialize_as = "json_object"
        cls._encode.handler = handler
        cls._encode.suppress = suppress or []
        cls._encode.exclude_nulls = exclude_nulls
        cls._encode.__type__ = cls_type or cls.__name__                       
        return __inspect_for_handler(cls)
    return wrapper


def to_list(handler=None):
    """
    If your class instances should serialize into a JSON list decorate it
    with :func:`to_list`. By default The python built in :class:`list` will
    be called with your class instance as its argument. ie **list(obj)**.
    This means your class needs to define the ``__iter__`` method.
    
    Here is an example::
        
        @to_object(suppress=["__type__"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        @to_list()
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
        
    Encoding ``people`` produces this JSON::
    
        [
            {"first_name": "Luke", "last_name": "Skywalker"}, 
            {"first_name": "Darth", "last_name": "Vader"}, 
            {"first_name": "Obi-Wan", "last_name": "Kenobi"}
        ]    
    
    .. versionadded:: 0.6.0 You can now specify a custom handler callable
       with the ``handler`` kw argument. It should accept one argument, your
       class instance. You can also use the :func:`jsonweb.encode.handler`
       decorator to mark one of the class's methods as the list handler.
            
    """
    def wrapper(cls):
        cls._encode = EncodeArgs()
        cls._encode.serialize_as = "json_list"
        cls._encode.handler = handler
        cls._encode.__type__ = cls.__name__        
        return __inspect_for_handler(cls)
    return wrapper


class JsonWebEncoder(json.JSONEncoder):
    """
    This :class:`json.JSONEncoder` subclass is responsible for encoding
    instances of classes that have been decorated with :func:`to_object` or
    :func:`to_list`. Pass :class:`JsonWebEncoder` as the value for the
    ``cls`` keyword argument to :func:`json.dump` or :func:`json.dumps`.
    
    Example::
    
        json.dumps(obj_instance, cls=JsonWebEncoder)
    
    Using :func:`dumper` is a shortcut for the above call to
    :func:`json.dumps` ::
    
        dumper(obj_instance) #much nicer!
                
    """
    
    _DT_FORMAT = "%Y-%m-%dT%H:%M:%S"
    _D_FORMAT = "%Y-%m-%d"

    def __init__(self, **kw):
        self.__hard_suppress = kw.pop("suppress", [])
        self.__exclude_nulls = kw.pop("exclude_nulls", None)
        self.__handlers = kw.pop("handlers", {})
        if not isinstance(self.__hard_suppress, list):
            self.__hard_suppress = [self.__hard_suppress]
        json.JSONEncoder.__init__(self, **kw)
        
    def default(self, o):        
        try:
            e_args = getattr(o, "_encode")
        except AttributeError:
            pass
        else:
            # Passed in handlers take precedence.
            if e_args.__type__ in self.__handlers:
                return self.__handlers[e_args.__type__](o)
            elif e_args.handler:
                if e_args.handler_is_instance_method:
                    return getattr(o, e_args.handler)()
                return e_args.handler(o)
            elif e_args.serialize_as == "json_object":
                return self.object_handler(o)
            elif e_args.serialize_as == "json_list":
                return self.list_handler(o)
            
        if isinstance(o, datetime.datetime):
            return o.strftime(self._DT_FORMAT)
        if isinstance(o, datetime.date):
            return o.strftime(self._D_FORMAT)
        return json.JSONEncoder.default(self, o)
    
    def object_handler(self, obj):
        """
        Handles encoding instance objects of classes decorated by
        :func:`to_object`. Returns a dict containing all the key/value pairs
        in ``obj.__dict__``. Excluding attributes that
        
        * start with an underscore.
        * were specified with the ``suppress`` keyword argument.
        
        The returned dict will be encoded into JSON.
        
        .. note::
        
            Override this method if you wish to change how ALL objects are
            encoded into JSON objects.
            
        """
        suppress = obj._encode.suppress
        if self.__exclude_nulls is not None:
            exclude_nulls = self.__exclude_nulls
        else:
            exclude_nulls = obj._encode.exclude_nulls
        json_obj = {}
        
        def suppressed(key):
            return key in suppress or key in self.__hard_suppress        
        
        for attr in dir(obj):
            if not attr.startswith("_") and not suppressed(attr):
                value = getattr(obj, attr)
                if value is None and exclude_nulls:
                    continue
                if not isinstance(value, types.MethodType):
                    json_obj[attr] = value
        if not suppressed("__type__"):
            json_obj["__type__"] = obj._encode.__type__
        return json_obj

    def list_handler(self, obj):
        """
        Handles encoding instance objects of classes decorated by
        :func:`to_list`. Simply calls :class:`list` on ``obj``.
        
        .. note::
        
            Override this method if you wish to change how ALL objects are
            encoded into JSON lists.
                
        """        
        return list(obj)


def dumper(obj, **kw):
    """
    JSON encode your class instances by calling this function as you would
    call :func:`json.dumps`. ``kw`` args will be passed to the underlying
    json.dumps call.

    :param handlers: A dict of type name/handler callable to use. 
     ie {"Person:" person_handler}
     
    :param cls: To override the given encoder. Should be a subclass 
     of :class:`JsonWebEncoder`.
     
    :param suppress: A list of extra fields to suppress (as well as those
     suppressed by the class).
     
    :param exclude_nulls: Set True to suppress keys with null (None) values
     from the JSON output. Defaults to False.
    """
    return json.dumps(obj, cls=kw.pop("cls", JsonWebEncoder), **kw)

