"""
:mod:`jsonweb.schema` provides a layer of validation before :mod:`json.decode` returns your object instances.
It can also be used simply to validate the resulting python data structures returned from :func:`json.loads`. Here
is an example of validating the structure of a python dict::

    >>> from jsonweb.schema import ObjectSchema, ValidationError
    >>> from jsonweb.schema.validators import String
    
    >>> class PersonSchema(ObjectSchema):
    ...     first_name = String()
    ...     last_name = String()
        
    >>> try:
    ...     PersonSchema().validate({"first_name": "shawn"})
    ... except ValidationError, e:
    ...     print e.errors
    {"last_name": "Missing required parameter."}
    
Validating plain old python data structures is fine, but the more interesting exercise is tying
a schema to a class definition::

    >>> from jsonweb.decode import from_object, loader
    >>> from jsonweb.schema import ObjectSchema, ValidationError
    >>> from jsonweb.schema.validators import String, Integer, EnsureType
    
    >>> class PersonSchema(ObjectSchema):
    ...    id = Integer()
    ...    first_name = String()
    ...    last_name = String()
    ...    gender = String(optional=True)
    ...    job = EnsureType("Job")

You can make any field optional by setting ``optional`` to :class:`True`.  

.. warning::

    The field is only optional at the schema level. If you've bound a schema to
    a class via :func:`from_object` and the underlying class requires that field a
    :class:`ObjectAttributeError` will be raised if missing.
    
As you can see its fine to pass a class name as a string, which we have done for 
the :class:`Job` class above. We must later define :class:`Job` and decorate it 
with :func:`jsonweb.decode.from_object` ::

    >>> class JobSchema(ObjectSchema):
    ...    id = Integer()
    ...    title = String()    
    
    >>> @from_object(schema=JobSchema)
    ... class Job(object):
    ...     def __init__(self, id, title):
    ...         self.id = id
    ...         self.title = title
    
    >>> @from_object(schema=PersonSchema)
    ... class Person(object):
    ...     def __init__(self, first_name, last_name, job, gender=None):
    ...         self.first_name = first_name
    ...         self.last_name = last_name
    ...         self.gender = gender
    ...         self.job = job
    ...     def __str__(self):
    ...         return '<Person name="%s" job="{0}">'.format(
    ...             " ".join((self.first_name, self.last_name)),   
    ...             self.job.title
    ...         )
    
    >>> person_json = '''
    ...     {
    ...         "__type__": "Person",
    ...         "id": 1,    
    ...         "first_name": "Bob",
    ...         "last_name": "Smith",
    ...         "job": {"__type__": "Job", "id": 5, "title": "Police Officer"},
    ...     }'''
    ...
    
    >>> person = loader(person_json)
    >>> print person
    <Person name="Bob" job="Police Officer">
    


"""
from jsonweb.schema.base import ObjectSchema, ValidationError, bind_schema