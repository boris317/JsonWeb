import json
import unittest


class TestJsonWebObjectDecoder(unittest.TestCase):
    def setUp(self):
        from jsonweb.decode import decode
        decode.handlers = {}
        
    def test_decodes_to_class_instance(self):
        from jsonweb.decode import from_object, object_hook
                
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                                
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams"}'
        person = json.loads(json_str, object_hook=object_hook)
        
        self.assertTrue(isinstance(person, Person))        
        self.assertEqual(person.first_name, "shawn")
        self.assertEqual(person.last_name, "adams")  
        
    def test_supplied_handler_decodes_to_class_instance(self):
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
        
    def test_class_kw_args_are_optional(self):
        from jsonweb.decode import from_object, object_hook        
        """
        Test that class keyword agruments are optional
        """
                
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name, job=None):
                self.first_name = first_name
                self.last_name = last_name
                self.job = job
                                
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams"}'
        person = json.loads(json_str, object_hook=object_hook)
        
        self.assertTrue(isinstance(person, Person))        
        self.assertEqual(person.first_name, "shawn")
        self.assertEqual(person.last_name, "adams")
        self.assertEqual(person.job, None)
        
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams", "job": "Jedi Knight"}'
        person = json.loads(json_str, object_hook=object_hook)
        self.assertEqual(person.job, "Jedi Knight")
        
    def test_ignores_extra_keys_in_json(self):
        from jsonweb.decode import from_object, object_hook
                
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                                
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams", "no_such_key": "hello"}'
        person = json.loads(json_str, object_hook=object_hook)
        
        self.assertTrue(isinstance(person, Person))        
        self.assertEqual(person.first_name, "shawn")
        self.assertEqual(person.last_name, "adams")
        
    def test_bad__init__raises_error(self):
        from jsonweb.decode import from_object, object_hook, JsonWebError      
        """
        Test that if a class has a no argument __init__ method or a *args/**kw only __init__
        method a JsonWebError is raised.
        """
        with self.assertRaises(JsonWebError) as context:
            @from_object()
            class Person(object):
                def __init__(self):
                    self.first_name = None
                    self.last_name = None
                    
        self.assertEqual(
            str(context.exception), 
            "Unable to generate an object_hook handler from Person's `__init__` method."
        )
        
    def test_supplied_handler_missing_required_attrs_raise_error(self):
        """
        KeyErrors raised from within supplied object handlers should be caught and
        turned into ObjectAttributeErrors.
        """
        
        from jsonweb.decode import from_object, object_hook, ObjectAttributeError
        
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
                
        json_str = '{"__type__": "Person", "first_name": "shawn"}'
        with self.assertRaises(ObjectAttributeError) as context:
            person = json.loads(json_str, object_hook=object_hook)
            
        exc = context.exception
        
        self.assertEqual(exc.extras["attribute"], "last_name")
        self.assertEqual(str(exc), "Missing last_name attribute for Person.")
            
        
    def test_generated_handler_missing_required_attrs_raise_error(self):
        """
        KeyErrors raised from within JsonWebObjectHandler should be caught and
        turned into ObjectAttributeErrors.
        """
        
        from jsonweb.decode import from_object, object_hook, ObjectAttributeError
                
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        json_str = '{"__type__": "Person", "first_name": "shawn"}'
        with self.assertRaises(ObjectAttributeError) as context:
            person = json.loads(json_str, object_hook=object_hook)
            
        exc = context.exception
        
        self.assertEqual(exc.extras["attribute"], "last_name")
        self.assertEqual(str(exc), "Missing last_name attribute for Person.")        
                