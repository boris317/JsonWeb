import json
import unittest
from jsonweb import dumper, to_object, from_object, loader, encode
from jsonweb.encode import to_list, JsonWebEncoder


class TestJsonEncode(unittest.TestCase):
    def test_json_object_decorator(self):

        @to_object(suppress=["foo", "__type__"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
        
        person = Person("shawn", "adams")
        json_obj = json.loads(dumper(person))
        
        self.assertEqual(json_obj, {"first_name": "shawn", "last_name": "adams"})
        
    def test_json_list_decorator(self):

        @to_list()
        class NickNames(object):
            def __init__(self, nicknames):
                self.nicknames = nicknames

            def __iter__(self):
                return iter(self.nicknames)
            
        @to_object(suppress=["foo", "__type__"])
        class Person(object):
            def __init__(self, first_name, last_name, nicknames=[]):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                self.nicknames = NickNames(nicknames)
        
        person = Person("shawn", "adams", ["Boss", "Champ"])
        json_obj = json.loads(dumper(person))
        
        self.assertEqual(json_obj, {
            "first_name": "shawn",
            "last_name": "adams",
            "nicknames": ["Boss", "Champ"]
        })
        
    def test_subclass_json_web_encoder(self):
        message = []

        class MyJsonWebEncoder(JsonWebEncoder):
            def object_handler(self, obj):
                message.append("my_object_handler")
                suppress = obj._encode.suppress
                json_obj = dict([(k, v) for k, v in obj.__dict__.items()
                                 if not k.startswith("_") and k not in suppress])
                if "__type__" not in suppress:
                    json_obj["__type__"] = obj._encode.__type__
                return json_obj
        
        @to_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
        
        person = Person("shawn", "adams")
        json_obj = json.loads(dumper(person, cls=MyJsonWebEncoder))
        
        self.assertEqual(json_obj, {
            "__type__": "Person",
            "first_name": "shawn",
            "last_name": "adams"
        })
        self.assertEqual(message[0], "my_object_handler")
        
    def test_methods_dont_get_serialized(self):

        @to_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                
            def foo_method(self):
                return self.foo

        person = Person("shawn", "adams")
        # the dumper call with actually fail if it tries to
        # serialize a method type.
        self.assertIsInstance(dumper(person), str)

    def test_supplied_obj_handler(self):

        def person_handler(obj):
            return {"FirstName": obj.first_name, "LastName": obj.last_name}
        
        @to_object(handler=person_handler)
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
        
        person = Person("shawn", "adams")
        json_obj = json.loads(dumper(person))
        
        self.assertEqual(json_obj, {"FirstName": "shawn", "LastName": "adams"})
        
    def test_stacked_decorators(self):

        def person_handler(cls, obj):
            return cls(
                obj['first_name'],
                obj['last_name']
            )                
                
        @to_object(suppress=["foo"])
        @from_object(person_handler)
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("shawn", "adams")
        json_str = dumper(person)
        del person
        person = loader(json_str)
        self.assertTrue(isinstance(person, Person))
        
    def test_attributes_are_suppressed(self):

        @to_object(suppress=["foo"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("shawn", "adams")                 
        json_obj = json.loads(dumper(person))
        self.assertTrue("foo" not in json_obj)
                
    def test_suppress__type__attribute(self):

        @to_object(suppress=["__type__"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("shawn", "adams")                 
        json_obj = json.loads(dumper(person))  
        self.assertTrue("__type__" not in json_obj)
        
    def test_suppress_kw_arg_to_dumper(self):

        @to_object(suppress=["foo"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("shawn", "adams")                 
        json_obj = json.loads(dumper(person))
        
        self.assertTrue("foo" not in json_obj)
        self.assertTrue("first_name" in json_obj)
        self.assertTrue("last_name" in json_obj)
        
        json_obj = json.loads(dumper(person, suppress="first_name"))
        self.assertTrue("foo" not in json_obj)                
        self.assertTrue("first_name" not in json_obj)
        self.assertTrue("last_name" in json_obj)

    def test_exclude_nulls_kw_arg_to_dumper(self):

        @to_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("shawn", None)                 
        json_obj = json.loads(dumper(person, exclude_nulls=True))
        self.assertTrue("last_name" not in json_obj)
        
    def test_exclude_nulls_kw_args_to_object(self):

        @to_object(exclude_nulls=True)
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("shawn", None)                 
        json_obj = json.loads(dumper(person))
        self.assertTrue("last_name" not in json_obj)
        
    def test_exclude_nulls_on_dumper_trumps_to_object(self):

        @to_object(exclude_nulls=True)
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("shawn", None)                 
        json_obj = json.loads(dumper(person, exclude_nulls=False))
        self.assertTrue("last_name" in json_obj)
     
    def test_supplied_handlers_kw_to_dumper(self):

        def person_handler(obj):
            return {"FirstName": obj.first_name,
                    "LastName": obj.last_name,
                    "Titles": obj.titles}

        def titles_handler(obj):
            return obj.titles
        
        @to_object()
        class Person(object):
            def __init__(self, first_name, last_name, titles=None):
                self.first_name = first_name
                self.last_name = last_name
                self.titles = titles
                
        @to_list()
        class Titles(object):
            def __init__(self, *titles):
                self.titles = titles

        person = Person("Joe", "Smith", Titles("Mr", "Dr"))
        json_obj = json.loads(dumper(person, handlers={
            "Person": person_handler,
            "Titles": titles_handler
        }))
        
        self.assertEqual(json_obj, {
            "FirstName": "Joe",
            "LastName": "Smith",
            "Titles": ["Mr", "Dr"]
        })
        
    def test_handler_decorator_for_object(self):

        @to_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
            @encode.handler   
            def to_json(self):
                return {"FirstName": self.first_name, "LastName": self.last_name}                
                
        person = Person("shawn", "adams")
        json_obj = json.loads(encode.dumper(person))
        
        self.assertEqual(json_obj, {"FirstName": "shawn", "LastName": "adams"})
        
    def test_handler_decorator_for_list(self):

        @encode.to_list()
        class ValueList(object):
            def __init__(self, *values):
                self.values = values
            @encode.handler
            def to_list(self):
                return self.values
            
        self.assertEqual(encode.dumper(ValueList(1 ,2, 3)), "[1, 2, 3]")
