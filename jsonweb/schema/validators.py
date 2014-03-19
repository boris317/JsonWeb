"""
Validators for use in :mod:`jsonweb.schema`.
"""
import inspect
import re
from datetime import datetime

from jsonweb.py3k import basestring, items
from jsonweb.exceptions import JsonWebError
from jsonweb.schema.base import BaseValidator, _Errors, ValidationError, \
    cls_name, isinstance_or_raise


class Dict(BaseValidator):
    """
    Validates a dict of things.
    """

    def __init__(self, validator, key_validator=None, **kw):
        super(Dict, self).__init__(error_type="invalid_dict", **kw)
        self.validator = to_instance(validator)
        self.key_validator = to_instance(key_validator) or String()
        assert isinstance(self.key_validator, String)

    def _validate(self, obj):
        isinstance_or_raise(obj, dict)
        errors = _Errors({})
        validated_obj = {}

        for k, v in items(obj):
            if not self._key_is_valid(k, errors):
                continue
            try:
                validated_obj[k] = get_validator(self.validator).validate(v)
            except ValidationError as e:
                errors.add_error(e, key=k, error_type="invalid_dict_value")

        errors.raise_if_errors("Error validating dict.",
                               error_type=self.error_type)
        return validated_obj

    def _key_is_valid(self, key, errors):
        if self.key_validator is None:
            return True
        try:
            self.key_validator.validate(key)
        except ValidationError as e:
            errors.add_error(e, key=key, error_type="invalid_dict_key")
            return False
        return True


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
        super(List, self).__init__(error_type="invalid_list", **kw)
        self.validator = to_instance(validator)

    def _validate(self, item):
        isinstance_or_raise(item, list)
        validated_objs = []
        errors = _Errors([])

        for i, obj in enumerate(item):
            try:
                validated_objs.append(
                    get_validator(self.validator).validate(obj)
                )
            except ValidationError as e:
                errors.add_error(e, error_type="invalid_list_item", index=i)

        errors.raise_if_errors("Error validating list.",
                               error_type=self.error_type)
        return validated_objs

    def to_json(self):
        return super(List, self).to_json()


def to_instance(obj):
    return inspect.isclass(obj) and obj() or obj


def get_validator(validator):
    # We must manually invoke the descriptor protocol so that
    # any string names passed to EnsureType get translated to
    # an actual class.
    if isinstance(validator, EnsureType):
        return validator.__get__(None, List)
    return validator


class EnsureType(BaseValidator):
    """
    Validates something is a certain type ::

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
        super(EnsureType, self).__init__(
            error_type=kw.pop("error_type", "invalid_type"), **kw
        )
        self.__type = _type
        #``_type`` can be a string. This way you can reference a class
        #that may not be defined yet. In this case we must explicitly
        #set type_name or an instance error is raised inside ``__type_name``
        if isinstance(_type, str):
            type_name = _type
        self.__type_name = type_name or self.__type_name(_type)

    def _validate(self, item):
        if not isinstance(item, self.__type):
            self.raise_error("Expected {0} got {1} instead.",
                             self.__type_name, cls_name(item))
        return item

    def __type_name(self, _type):
        if isinstance(_type, tuple):
            return "one of ({0})".format(", ".join((t.__name__ for t in _type)))
        return _type.__name__

    def __get__(self, obj, type=None):

        if type is None:
            return self
        if not isinstance(self.__type, str):
            return self

        from jsonweb.decode import _default_object_handlers
        #``_type`` was a string and now we must get the actual class
        handler = _default_object_handlers.get(self.__type)

        if not handler:
            raise JsonWebError("Cannot find class {0}.".format(self.__type))

        return EnsureType(
            handler[1],
            type_name=self.__type_name,
            optional=(not self.required),
            nullable=self.nullable
        )

    def to_json(self, **kw):
        return super(EnsureType, self).to_json(
            type=self.__type_name, **kw
        )


class String(EnsureType):
    """
    Validates something is a string ::

        >>> String().validate("foo")
        ... 'foo'
        >>> String().validate(1)
        Traceback (most recent call last):
            ...
        ValidationError: Expected str got int instead.

    Specify a maximum length ::

        >>> String(max_len=3).validate("foobar")
        Traceback (most recent call last):
        ...
        ValidationError: String exceeds max length of 3.

    Specify a minimum length ::

        >>> String(min_len=3).validate("fo")
        Traceback (most recent call last):
        ...
        ValidationError: String must be at least length 3.

    """
    def __init__(self, min_len=None, max_len=None, **kw):
        super(String, self).__init__(basestring, type_name="str",
                                     error_type="invalid_str", **kw)
        self.max_len = max_len
        self.min_len = min_len

    def _validate(self, item):
        value = super(String, self)._validate(item)
        if self.min_len and len(value) < self.min_len:
            self.raise_error("String must be at least length {0}.", self.min_len)
        if self.max_len and len(value) > self.max_len:
            self.raise_error("String exceeds max length of {0}.", self.max_len)
        return value


class Regex(String):
    """
    .. versionadded:: 0.6.3 Validates a string against a regular expression ::

        >>> Regex(r"^foo").validate("barfoo")
        Traceback (most recent call last):
        ...
        ValidationError: String does not match pattern '^foo'.
    """

    def __init__(self, regex, **kw):
        super(Regex, self).__init__(**kw)
        self.regex = re.compile(regex)

    def _validate(self, item):
        value = super(Regex, self)._validate(item)
        if self.regex.match(value) is None:
            self.raise_error("String does not match pattern '{0}'.",
                             self.regex.pattern)
        return value


class Integer(EnsureType):
    """ Validates something in an integer """
    def __init__(self, **kw):
        super(Integer, self).__init__(int, **kw)


class Float(EnsureType):
    """ Validates something is a float """
    def __init__(self, **kw):
        super(Float, self).__init__(float, **kw)


class Boolean(EnsureType):
    """ Validates something is a Boolean (True/False)"""
    def __init__(self, **kw):
        super(Boolean, self).__init__(bool, **kw)


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
        super(Number, self).__init__((float, int), type_name="number",
                                     error_type="invalid_number", **kw)


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
    def __init__(self, format="%Y-%m-%d %H:%M:%S", **kw):
        super(DateTime, self).__init__(error_type="invalid_datetime", **kw)
        self.format = format

    def _validate(self, item):
        try:
            return datetime.strptime(item, self.format)
        except ValueError as e:
            self.raise_error(str(e))

    def to_json(self):
        return super(DateTime, self).to_json(
            type="DateTime",
            format=self.format
        )


class OneOf(BaseValidator):
    """
    .. versionadded:: 0.6.4
        Validates something is a one of a list of allowed values::

        >>> OneOf("a", "b", "c").validate(1)
        Traceback (most recent call last):
            ...
        ValidationError: Expected one of (a, b, c) got 1 instead.
    """
    def __init__(self, *values, **kw):
        super(OneOf, self).__init__(error_type="not_one_of", **kw)
        self.allowed_values = values

    def _validate(self, item):

        def stringify(item):
            if isinstance(item, str):
                return "'{0}'".format(item)
            return str(item)

        if item in self.allowed_values:
            return item

        self.raise_error("Expected one of {0} but got {1} instead.",
                         self.allowed_values, stringify(item))


class SubSetOf(BaseValidator):
    """
    .. versionadded:: 0.6.4 Validates a list is subset of another list::

        >>> SubSetOf([1, 2, 3, 4]).validate([1, 4])
        ... [1, 4]
        >>> SubSetOf([1, 2, 3, 4]).validate([1,5])
        Traceback (most recent call last):
            ...
        ValidationError: [1, 5] is not a subset of [1, 2, 3, 4].
    """

    def __init__(self, super_set, **kw):
        super(SubSetOf, self).__init__(error_type="not_a_sub_set_of", **kw)
        self.super_set = super_set

    def _validate(self, sub_set):
        if set(sub_set).issubset(self.super_set):
            return sub_set
        self.raise_error("{0} is not a subset of {1}", sub_set, self.super_set)
