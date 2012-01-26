import json
import unittest

class TestJsonEnecode(unittest.TestCase):
    def test_json_object_decorator(self):
        from jsonweb.encode import to_object, JsonWebEncoder
                
        @to_object(suppress=["foo", "__type__"])
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
        
        person = Person("shawn", "adams")
        json_obj = json.loads(json.dumps(person, cls=JsonWebEncoder))
        
        self.assertEqual(json_obj, {"first_name": "shawn", "last_name": "adams"})
        
    def test_subclass_json_web_encoder(self):
        from jsonweb.encode import to_object, JsonWebEncoder
        
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
        json_obj = json.loads(json.dumps(person, cls=MyJsonWebEncoder))
        
        self.assertEqual(json_obj, {"__type__": "Person", "first_name": "shawn", "last_name": "adams"})
        self.assertEqual(message[0], "my_object_handler")
        
    def test_supplied_obj_handler(self):
        from jsonweb.encode import to_object, JsonWebEncoder
                
        def person_handler(obj):
            return {"FirstName": obj.first_name, "LastName": obj.last_name}
        
        @to_object(handler=person_handler)
        class Person(object):
            def __init__(self, first_name, last_name):
                self.foo = "bar"
                self.first_name = first_name
                self.last_name = last_name
        
        person = Person("shawn", "adams")
        json_obj = json.loads(json.dumps(person, cls=JsonWebEncoder))
        
        self.assertEqual(json_obj, {"FirstName": "shawn", "LastName": "adams"})        
        
    def test_stacked_decorators(self):
        from jsonweb.encode import to_object, JsonWebEncoder
        from jsonweb.decode import from_object, object_hook
                
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
        json_str = json.dumps(person, cls=JsonWebEncoder)
        del person
        person = json.loads(json_str, object_hook=object_hook)
        self.assertTrue(isinstance(person, Person))
                 
        