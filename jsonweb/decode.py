"""
Sometimes it would be nice to have :func:`json.loads` return class instances.
For example if you do something like this ::

    person = json.loads('''
    {
        "__type__": "Person",
        "first_name": "Shawn",
        "last_name": "Adams"
    }
    ''')
    
it would be pretty cool if instead of ``person`` being a :class:`dict` it was
an instance of a class we defined called :class:`Person`. Luckily the python
standard :mod:`json` module provides support for *class hinting* in the form
of the ``object_hook`` keyword argument accepted by :func:`json.loads`.

The code in :mod:`jsonweb.decode` uses this ``object_hook`` interface to
accomplish the awesomeness you are about to witness. Lets turn that
``person`` :class:`dict` into a proper :class:`Person` instance. ::

    >>> from jsonweb.decode import from_object, loader

    >>> @from_object()
    ... class Person(object):
    ...     def __init__(self, first_name, last_name):
    ...         self.first_name = first_name
    ...         self.last_name = last_name
    ...

    >>> person = loader('''
    ... {
    ...     "__type__": "Person",
    ...     "first_name": "Shawn",
    ...     "last_name": "Adams"
    ... }
    ... ''')

    >>> print type(person)
    <class 'Person'>
    >>> print person.first_name
    "Shawn"

But how was :mod:`jsonweb` able to determine how to instantiate the
:class:`Person` class? Take a look at the :func:`from_object` decorator for a
detailed explanation.
"""

import inspect
import json
from contextlib import contextmanager
from jsonweb.py3k import items

from jsonweb.validators import EnsureType
from jsonweb.exceptions import JsonWebError
from jsonweb._local import LocalStack

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

# Thread local object stack used by :func:`ensure_type`
_as_type_context = LocalStack()


class JsonDecodeError(JsonWebError):
    """
    Raised for malformed json.
    """
    def __init__(self, message, **extras):
        JsonWebError.__init__(self, message, **extras)


class ObjectDecodeError(JsonWebError):
    """
    Raised when python containers (dicts and lists) cannot be decoded into
    complex types. These exceptions are raised from within an ObjectHook
    instance.
    """
    def __init__(self, message, **extras):
        JsonWebError.__init__(self, message, **extras)


class ObjectAttributeError(ObjectDecodeError):
    def __init__(self, obj_type, attr):
        ObjectDecodeError.__init__(
            self,
            "Missing {0} attribute for {1}.".format(attr, obj_type),
            obj_type=obj_type, 
            attribute=attr
        )


class ObjectNotFoundError(ObjectDecodeError):
    def __init__(self, obj_type):
        ObjectDecodeError.__init__(
            self,
            "Cannot decode object {0}. No such object.".format(obj_type),
            obj_type=obj_type,
        )


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


class _ObjectHandlers(object):
    def __init__(self):
        self.__handlers = {}
        self.__deferred_updates = {}
        
    def add_handler(self, cls, handler, type_name=None, schema=None):
        name = type_name or cls.__name__
        self.__handlers[name] = self.__merge_tuples(
            self.__deferred_updates.get(name, (None,)*3),            
            (handler, cls, schema)
        )
        
    def get(self, name):
        """
        Get a handler tuple. Return None if no such handler.
        """
        return self.__handlers.get(name)
    
    def set(self, name, handler_tuple):
        """
        Add a handler tuple (handler, cls, schema)
        """
        self.__handlers[name] = handler_tuple
    
    def clear(self):
        self.__handlers = {}
        self.__deferred_updates = {}
        
    def update_handler(self, name, cls=None, handler=None, schema=None):
        """
        Modify cls, handler and schema for a decorated class. 
        """
        handler_tuple = self.__handlers[name]
        self.set(name, self.__merge_tuples((handler, cls, schema), 
                                           handler_tuple))
                 
    def update_handler_deferred(self, name, cls=None,
                                handler=None, schema=None):
        """
        If an entry does not exist in __handlers an entry will be added to
        __deferred_updates instead. Then when add_handler is finally called
        values will be updated accordingly. Items in __deferred_updates will
        take precedence over those passed into add_handler.
        """
        if name in self.__handlers:
            self.update_handler(name, cls, handler, schema)
            return
        d = self.__deferred_updates.get(name, (None,)*3)
        self.__deferred_updates[name] = self.__merge_tuples(
            (handler, cls, schema), d)
        
    def copy(self):
        handler_copy = _ObjectHandlers()
        [handler_copy.set(n, t) for n, t in self]
        return handler_copy
    
    def __merge_tuples(self, a_tuple, b_tuple):
        """
        "Merge" two tuples of the same length. a takes precedence over b.
        """        
        if len(a_tuple) != len(b_tuple):
            raise ValueError("Iterators differ in length.")
        return tuple([(a or b) for a, b in zip(a_tuple, b_tuple)])
    
    def __contains__(self, handler_name):
        return handler_name in self.__handlers
    
    def __getitem__(self, handler):
        return self.__handlers[handler]
    
    def __iter__(self):
        for name, handler_tuple in items(self.__handlers):
            yield name, handler_tuple


class ObjectHook(object):
    """
    This class does most of the work in managing the handlers that decode the
    json into python class instances. You should not need to use this class
    directly. :func:`object_hook` is responsible for instantiating and using it.
    """

    def __init__(self, handlers, validate=True):
        self.handlers = handlers
        self.validate = validate
            
    def decode_obj(self, obj):
        """        
        This method is called for every dict decoded in a json string. The
        presence of the key ``__type__`` in ``obj`` will trigger a lookup in
        ``self.handlers``. If a handler is not found for ``__type__`` then an
        :exc:`ObjectNotFoundError` is raised. If a handler is found it will
        be called with ``obj`` as it only argument. If an :class:`ObjectSchema`
        was supplied for the class, ``obj`` will first be validated then passed
        to handler. The handler should return a new python instant of type ``__type__``.
        """
        if "__type__" not in obj:
            return obj
        
        obj_type = obj["__type__"]
        try:
            factory, cls, schema = self.handlers[obj_type]
        except KeyError:
            raise ObjectNotFoundError(obj_type)
                
        if schema and self.validate:
            obj = schema().validate(obj)
        try:
            return factory(cls, obj)
        except KeyError as e:
            raise ObjectAttributeError(obj_type, e.args[0])
        

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
        raise JsonWebError("Unable to generate an object_hook handler from "
                           "{0}'s `__init__` method.".format(cls.__name__))
    args, kw = get_arg_spec(cls.__init__)

    return JsonWebObjectHandler(args, kw or None)

_default_object_handlers = _ObjectHandlers()


def from_object(handler=None, type_name=None, schema=None):
    """
    Decorating a class with :func:`from_object` will allow :func:`json.loads`
    to return instances of that class.
    
    ``handler`` is a callable that should return your class instance. It
    receives two arguments, your class and a python dict. Here is an
    example::

        >>> from jsonweb.decode import from_object, loader
        >>> def person_decoder(cls, obj):
        ...    return cls(
        ...        obj["first_name"],
        ...        obj["last_name"]
        ...    )
        ...
        >>> @from_object(person_decoder)        
        ... class Person(object):
        ...     def __init__(self, first_name, last_name):
        ...         self.first_name
        ...         self.last_name = last_name
        ...
        >>> person_json = '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}'
        >>> person = loader(person_json)
        >>> person
        <Person object at 0x1007d7550>
        >>> person.first_name
        'Shawn'
        
    The ``__type__`` key is very important. Without it :mod:`jsonweb` would
    not know which handler to delegate the python dict to. By default
    :func:`from_object` assumes ``__type__`` will be the class's ``__name__``
    attribute. You can specify your own value by setting the ``type_name``
    keyword argument ::
    
        @from_object(person_decoder, type_name="PersonObject")
        
    Which means the json string would need to be modified to look like this::
    
        '{"__type__": "PersonObject", "first_name": "Shawn", "last_name": "Adams"}'
        
    If a handler cannot be found for ``__type__`` an exception is raised ::

        >>> luke = loader('{"__type__": "Jedi", "name": "Luke"}')
        Traceback (most recent call last):
            ...
        ObjectNotFoundError: Cannot decode object Jedi. No such object.
        
    You may have noticed that ``handler`` is optional. If you do not specify
    a ``handler`` :mod:`jsonweb` will attempt to generate one. It will
    inspect your class's ``__init__`` method. Any positional arguments will
    be considered required while keyword arguments will be optional.
    
    .. warning::
    
        A handler cannot be generated from a method signature containing only
        ``*args`` and ``**kwargs``. The handler would not know which keys to
        pull out of the python dict.
    
    Lets look at a few examples::

        >>> from jsonweb import from_object
        >>> @from_object()
        ... class Person(object):
        ...     def __init__(self, first_name, last_name, gender):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
        ...         self.gender = gender

        >>> person_json = '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams", "gender": "male"}'
        >>> person = loader(person_json)
        
    What happens if we dont want to specify ``gender``::
            
        >>> person_json = '''{
        ...     "__type__": "Person", 
        ...     "first_name": "Shawn", 
        ...     "last_name": "Adams"
        ... }'''
        >>> person = loader(person_json)
        Traceback (most recent call last):
            ...        
        ObjectAttributeError: Missing gender attribute for Person.
        
    To make ``gender`` optional it must be a keyword argument::

        >>> from jsonweb import from_object
        >>> @from_object()
        ... class Person(object):
        ...     def __init__(self, first_name, last_name, gender=None):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
        ...         self.gender = gender
        
        >>> person_json = '{"__type__": "Person", "first_name": "Shawn", "last_name": "Adams"}'
        >>> person = loader(person_json)
        >>> print person.gender
        None
  
    You can specify a json validator for a class with the ``schema`` keyword agrument. 
    Here is a quick example::

        >>> from jsonweb import from_object
        >>> from jsonweb.schema import ObjectSchema
        >>> from jsonweb.validators import ValidationError, String
        >>> class PersonSchema(ObjectSchema):
        ...    first_name = String()
        ...    last_name = String()
        ...    gender = String(optional=True)
        ...
        >>> @from_object(schema=PersonSchema)
        ... class Person(object):
        ...     def __init__(self, first_name, last_name, gender=None):
        ...         self.first_name = first_name
        ...         self.last_name = last_name
        ...         self.gender = gender
        ...
        >>> person_json = '{"__type__": "Person", "first_name": 12345, "last_name": "Adams"}'
        >>> try:
        ...     person = loader(person_json)
        ... except ValidationError, e:
        ...     print e.errors["first_name"].message
        Expected str got int instead.
    
    Schemas are useful for validating user supplied json in web services or
    other web applications. For a detailed explanation on using schemas see
    the :mod:`jsonweb.schema`.
    """
    def wrapper(cls):
        _default_object_handlers.add_handler(
            cls, handler or get_jsonweb_handler(cls), type_name, schema
        )
        return cls
    return wrapper


def object_hook(handlers=None, as_type=None, validate=True):
    """
    Wrapper around :class:`ObjectHook`. Calling this function will configure
    an instance of :class:`ObjectHook` and return a callable suitable for
    passing to :func:`json.loads` as ``object_hook``.

    If you need to decode a JSON string that does not contain a ``__type__``
    key and you know that the JSON represents a certain object or list of
    objects you can use ``as_type`` to specify it ::
    
        >>> json_str = '{"first_name": "bob", "last_name": "smith"}'
        >>> loader(json_str, as_type="Person")
        <Person object at 0x1007d7550>
        >>> # lists work too
        >>> json_str = '''[
        ...     {"first_name": "bob", "last_name": "smith"},
        ...     {"first_name": "jane", "last_name": "smith"}
        ... ]'''
        >>> loader(json_str, as_type="Person")
        [<Person object at 0x1007d7550>, <Person object at 0x1007d7434>]
        
    .. note::
    
        Assumes every object WITHOUT a ``__type__``  kw is of 
        the type specified by ``as_type`` .
         
    ``handlers`` is a dict with this format::
    
        {"Person": {"cls": Person, "handler": person_decoder, "schema": PersonSchema)}
        
    If you do not wish to decorate your classes with :func:`from_object` you
    can specify the same parameters via the ``handlers`` keyword argument.
    Here is an example::
        
        >>> class Person(object):
        ...    def __init__(self, first_name, last_name):
        ...        self.first_name = first_name
        ...        self.last_name = last_name
        ...        
        >>> def person_decoder(cls, obj):
        ...    return cls(obj["first_name"], obj["last_name"])
            
        >>> handlers = {"Person": {"cls": Person, "handler": person_decoder}}
        >>> person = loader(json_str, handlers=handlers)
        >>> # Or invoking the object_hook interface ourselves
        >>> person = json.loads(json_str, object_hook=object_hook(handlers))
        
    .. note:: 
    
        If you decorate a class with :func:`from_object` you can override the
        ``handler`` and ``schema`` values later. Here is an example of
        overriding a schema you defined with :func:`from_object` (some code
        is left out for brevity)::

            >>> from jsonweb import from_object
            >>> @from_object(schema=PersonSchema)
            >>> class Person(object):
                ...
                
            >>> # and later on in the code...
            >>> handlers = {"Person": {"schema": NewPersonSchema}}
            >>> person = loader(json_str, handlers=handlers)
            
    If you need to use ``as_type`` or ``handlers`` many times in your code
    you can forgo using :func:`loader` in favor of configuring a "custom"
    object hook callable. Here is an example ::
                
        >>> my_obj_hook = object_hook(handlers)
        >>> # this call uses custom handlers
        >>> person = json.loads(json_str, object_hook=my_obj_hook)
        >>> # and so does this one ...
        >>> another_person = json.loads(json_str, object_hook=my_obj_hook)                                
    """
    if handlers:
        _object_handlers = _default_object_handlers.copy()
        for name, handler_dict in items(handlers):
            if name in _object_handlers:
                _object_handlers.update_handler(name, **handler_dict)
            else:
                _object_handlers.add_handler(
                    handler_dict.pop('cls'),
                    **handler_dict
                )
    else:
        _object_handlers = _default_object_handlers
               
    decode = ObjectHook(_object_handlers, validate)

    def handler(obj):
        if as_type and "__type__" not in obj:
            obj["__type__"] = as_type
        return decode.decode_obj(obj)

    return handler


def loader(json_str, **kw):
    """
    Call this function as you would call :func:`json.loads`. It wraps the
    :ref:`object_hook` interface and returns python class instances from JSON
    strings.
    
    :param ensure_type: Check that the resulting object is of type
        ``ensure_type``. Raise a ValidationError otherwise.          
    :param handlers: is a dict of handlers. see :func:`object_hook`.    
    :param as_type: explicitly specify the type of object the JSON
        represents. see :func:`object_hook`    
    :param validate: Set to False to turn off validation (ie dont run the
        schemas) during this load operation. Defaults to True.    
    :param kw: the rest of the kw args will be passed to the underlying
        :func:`json.loads` calls.
    
    
    """
    kw["object_hook"] = object_hook(
        kw.pop("handlers", None),
        kw.pop("as_type", None),
        kw.pop("validate", True)
    )
    
    ensure_type = kw.pop("ensure_type", _as_type_context.top)
    
    try:
        obj = json.loads(json_str, **kw)
    except ValueError as e:
        raise JsonDecodeError(e.args[0])
    
    if ensure_type:
        return EnsureType(ensure_type).validate(obj)
    return obj


@contextmanager
def ensure_type(cls):
    """
    This context manager lets you "inject" a value for ``ensure_type`` into
    :func:`loader` calls made in the active context. This will allow a
    :class:`~jsonweb.schema.ValidationError` to bubble up from the underlying
    :func:`loader` call if the resultant type is not of type ``ensure_type``.
    
    Here is an example ::
            
        # example_app.model.py
        from jsonweb.decode import from_object
        # import db model stuff
        from example_app import db
        
        @from_object()
        class Person(db.Base):
            first_name = db.Column(String)
            last_name = db.Column(String)
            
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name

                
        # example_app.__init__.py
        from example_app.model import session, Person
        from jsonweb.decode import from_object, ensure_type
        from jsonweb.schema import ValidationError
        from flask import Flask, request, abort

        app.errorhandler(ValidationError)
        def json_validation_error(e):
            return json_response({"error": e})
            
            
        def load_request_json():
            if request.headers.get('content-type') == 'application/json':
                return loader(request.data)
            abort(400)
            
            
        @app.route("/person", methods=["POST", "PUT"])
        def add_person():
            with ensure_type(Person):
                person = load_request_json()
            session.add(person)
            session.commit()
            return "ok"
            
        
    The above example is pretty contrived. We could have just made ``load_json_request``
    accept an ``ensure_type`` kw, but imagine if the call to :func:`loader` was burried 
    deeper in our api and such a thing was not possible.
    """
    _as_type_context.push(cls)
    try:
        yield None
    finally:
        _as_type_context.pop()