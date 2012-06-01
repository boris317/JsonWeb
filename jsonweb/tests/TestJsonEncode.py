import json
import unittest

class TestJsonEnecode(unittest.TestCase):
    def test_json_object_decorator(self):
        from jsonweb.encode import to_object, dumper
                
        @to_object(suppress=["foo", "__type__"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
        
        person = Person("shawn", "adams")
        json_obj = json.loads(dumper(person))
        
        self.assertEqual(json_obj, {"first_name": "shawn", "last_name": "adams"})
        
    def test_subclass_json_web_encoder(self):
        from jsonweb.encode import to_object, JsonWebEncoder, dumper
        
        message = []
        class MyJsonWebEncoder(JsonWebEncoder):
            def object_handler(self, obj):
                message.append("my_object_handler")
                suppress = obj._encode.suppress
                json_obj = dict([(k,v) for k,v in obj.__dict__.iteritems() if not k.startswith("_") and k not in suppress])
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
        
        self.assertEqual(json_obj, {"__type__": "Person", "first_name": "shawn", "last_name": "adams"})
        self.assertEqual(message[0], "my_object_handler")
        
    def test_supplied_obj_handler(self):
        from jsonweb.encode import to_object, dumper
                
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
        from jsonweb.encode import to_object, dumper
        from jsonweb.decode import from_object, loader
                
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
        from jsonweb.encode import to_object, dumper
        
        @to_object(suppress=["foo"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
                
        person = Person("shawn", "adams")                 
        json_obj = json.loads(dumper(person))
        self.assertTrue("foo" not in json_obj)
        
    def test_dumper_suppress_keyword(self):
        from jsonweb.encode import to_object, dumper
        
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