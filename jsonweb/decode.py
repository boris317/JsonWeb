"""
Sometimes it would be nice to have :func:`json.loads` return class instances. For example if you
do something like this ::

    person = json.loads('{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}')
    
it would be pretty cool if instead of ``person`` being a :class:`dict` it was an instance of a class we defined called :class:`Person`.
Luckily the python standard :mod:`json` module provides support for *class hinting* in the form of the ``object_hook`` keyword
argument accepted by :func:`json.loads`.

The code in :mod:`jsonweb.decode` uses this ``object_hook`` interface to accomplish the awesomeness you are about to witness.
Lets turn that ``person`` :class:`dict` into a proper :class:`Person` instance. ::

    >>> import json
    >>> from jsonweb.decode import from_obj, object_hook

    >>> @from_object()
    ... class Person(object):
    ...     def __init__(self, first_name, last_name):
    ...         self.first_name = first_name
    ...         self.last_name = last_name

    >>> person_json = '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}'
    >>> person = json.loads(person_json, object_hook=object_hook)

    >>> print type(person)
    <class 'Person'>
    >>> print person.first_name
    "Shawn"

But how was :mod:`jsonweb` able to determine how to instantiate the :class:`Person` class? Take a look 
at the :func:`from_object` decorator for a detailed explanation.
"""

import inspect
import json
from datetime import datetime

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

class JsonWebError(Exception):
    pass

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

class ObjectAttributeError(ObjectDecodeError):
    def __init__(self, obj, attr):
        ObjectDecodeError.__init__(self, 
            "Missing %s attribute for %s." % (attr, obj.__class__.__name__), 
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

class JsonWebObjectHandler(object):
    def __init__(self, args, kw_args=None):
        self.args = args
        self.kw_args = kw_args
        
    def __call__(self, cls, obj):
        cls_args = []
        cls_kw_args = {}
        
        for arg in self.args:
            cls_args.append(obj[arg])
            
        if self.kw_args:
            for key, default in self.kw_args:
                cls_kw_args[key] = obj.get(key, default)
                
        return cls(*cls_args, **cls_kw_args)
            
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
        of the key ``__type__`` in ``obj`` will trigger a lookup in ``self.handlers``. If a handler is
        not found for ``__type__`` then an :exc:`ObjectNotFoundError` is raised. If a handler is found it will
        be called with ``obj`` as it only argument. If all goes well it should return a new
        python instant of type ``__type__``.        
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

def get_arg_spec(func):
    arg_spec = inspect.getargspec(func)
    args = arg_spec.args
    
    try:   
        if args[0] == "self":
            del args[0]
    except IndexError:
        pass
    
    if not args:
        return None    
    
    kw_args = []
    if arg_spec.defaults:
        for default in reversed(arg_spec.defaults):
            kw_args.append((args.pop(), default))
        
    return args, kw_args

def get_jsonweb_handler(cls):
    arg_spec = get_arg_spec(cls.__init__)
    if arg_spec is None:
        raise JsonWebError("Unable to generate an object_hook handler from %s's `__init__` method." % cls.__name__)
    args, kw = get_arg_spec(cls.__init__)

    return JsonWebObjectHandler(args, kw or None)
    
decode = ObjectHook()

def from_object(handler=None, type_name=None, schema=None):
    """
    Decorating a class with :func:`from_object` will allow :func:`json.loads` to return
    instances of that class. 
    
    ``handler`` is a callable that should return your class instance. It 
    receives two arguments, your class and a python dict. Here is an example::
    
        >>> import json
        >>> from jsonweb.decode import from_object object_hook
        
        >>> def person_handler(cls, obj):
        ...    return cls(
        ...        obj["first_name"],
        ...        obj["last_name"]
        ...    )
        
        >>> from_object(person_handler)        
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name
        ...         self.last_name = last_name
        
        >>> person_json = '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}'
        >>> person = json.loads(person_json, object_hook=object_hook)
        >>> person
        <Person object at 0x1007d7550>
        
        >>> person.first_name
        'Shawn'
        
    The ``__type__`` key is very important. Without it :mod:`jsonweb` would not know which
    handler to delegate the python dict to. By default :func:`from_object` assumes ``__type__``
    will be the class's ``__name__`` attribute. You can specify your own value by setting
    the ``type_name`` keyword argument::
    
        @from_object(person_handler, "PersonObject")
        
    Which means the json string would need to be modified to look like this::
    
        '{"__type__": "PersonObject", "first_name": "Shawn", "last_name": "Adams"}'
        
    You may have noticed that ``handler`` is optional. If you do not specify a ``handler`` 
    :mod:`jsonweb` will attempt to generate one. It will inspect your class's ``__init__``
    method. Any positional arguments will be considered required while keyword arguments
    will be optional.
    
    .. warning::
    
        A handler cannot be generated from a method signature containing only ``*args`` and ``**kwargs``.
        The handler would not know which keys to pull out of the python dict.
    
    Lets look at a few examples::
            
        >>> @from_object()
        ... class Person(object):
        ...     def __init__(self, first_name, last_name, gender):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
        ...         self.gender = gender

        >>> person_json = '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams", "gender": "male"}'
        >>> person = json.loads(person_json, object_hook=object_hook)
        
    What happens if we dont want to specify ``gender``::
    
        >>> from jsonweb.decode import ObjectAttributeError
        
        >>> person_json = '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}'
        >>> try:
        ...     person = json.loads(person_json, object_hook=object_hook)
        ... except ObjectAttributeError, e:
        ...     print e
        Missing gender attribute for Person.
        
    To make ``gender`` optional it must be a keyword argument::
    
        >>> @from_object()
        ... class Person(object):
        ...     def __init__(self, first_name, last_name, gender=None):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
        ...         self.gender = gender
        
        >>> person_json = '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}'
        >>> person = json.loads(person_json, object_hook=object_hook)
        >>> print person.gender
        None
        
    You can specify a json validator for a class with the ``schema`` keyword agrument. See the 
    :mod:`jsonweb.schema` to learn how they are used.
    """
    def wrapper(cls):
        obj_handler = handler or get_jsonweb_handler(cls)
        decode.add_handler(cls, obj_handler, type_name, schema)
        return cls
    return wrapper

def object_hook(obj):
    """
    Very thin wrapper aound the module level instance of :class:`ObjectHook`. This is
    the callable you will pass into :func:`json.loads` for the keywoard argument
    ``object_hook``. 
    """
    return decode.decode_obj(obj)
