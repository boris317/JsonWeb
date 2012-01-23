import json
import unittest

class TestJsonDecode(unittest.TestCase):
    def test_decode_decorator(self):
        from jsonweb.decode import from_object, object_hook
        
        def person_handler(cls, obj):
            return cls(
                obj['first_name'],
                obj['last_name']
            )
        
        @from_object(person_handler)
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams"}'
        person = json.loads(json_str, object_hook=object_hook)
        
        self.assertTrue(isinstance(person, Person))