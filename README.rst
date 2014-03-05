JsonWeb 
========

.. image:: https://travis-ci.org/boris317/JsonWeb.png?branch=master
   :target: https://travis-ci.org/boris317/JsonWeb

Add JSON (de)serialization to your python objects ::

    >>> from jsonweb import decode, encode
    
    >>> @encode.to_object()
    ... @decode.from_object()
    ... class User(object):
    ...     def __init__(self, nick, email):
    ...         self.nick = nick
    ...         self.email = email
    
    >>> json_str = encode.dumper(User("cool_user123", "cool_user123@example.com"))
    >>> print json_str
    {"nick": "cool_user123", "__type__": "User", "email": "cool_user123@example.com"}
    
    >>> user = decode.loader(json_str)
    >>> print user.nick
    cool_user123
    >>> print user
    <User object at 0x10145e390>
    
.. note ::

    JsonWeb is still very much under development. Things will change.

See  `documentation <http://readthedocs.org/docs/jsonweb/en/latest/>`_

