import json
import unittest


class TestJsonWebObjectDecoder(unittest.TestCase):
    def setUp(self):
        from jsonweb.decode import _default_object_handlers
        _default_object_handlers.clear()
        
    def test_decodes_to_class_instance(self):
        from jsonweb.decode import from_object, loader
                
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                                
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams"}'
        person = loader(json_str)
        
        self.assertTrue(isinstance(person, Person))        
        self.assertEqual(person.first_name, "shawn")
        self.assertEqual(person.last_name, "adams")  
        
    def test_supplied_handler_decodes_to_class_instance(self):
        from jsonweb.decode import from_object, loader
        
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
        person = loader(json_str)
        
        self.assertTrue(isinstance(person, Person))
        
    def test_class_kw_args_are_optional(self):
        from jsonweb.decode import from_object, loader
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
        person = loader(json_str)
        
        self.assertTrue(isinstance(person, Person))        
        self.assertEqual(person.first_name, "shawn")
        self.assertEqual(person.last_name, "adams")
        self.assertEqual(person.job, None)
        
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams", "job": "Jedi Knight"}'
        person = loader(json_str)
        self.assertEqual(person.job, "Jedi Knight")
        
    def test_ignores_extra_keys_in_json(self):
        from jsonweb.decode import from_object, loader
                
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                                
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams", "no_such_key": "hello"}'
        person = loader(json_str)
        
        self.assertTrue(isinstance(person, Person))        
        self.assertEqual(person.first_name, "shawn")
        self.assertEqual(person.last_name, "adams")
        
    def test_bad__init__raises_error(self):
        from jsonweb.decode import from_object, JsonWebError      
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
        
        from jsonweb.decode import from_object, loader, ObjectAttributeError
        
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
            person = loader(json_str)
            
        exc = context.exception
        
        self.assertEqual(exc.extras["attribute"], "last_name")
        self.assertEqual(str(exc), "Missing last_name attribute for Person.")
            
        
    def test_generated_handler_missing_required_attrs_raise_error(self):
        """
        KeyErrors raised from within JsonWebObjectHandler should be caught and
        turned into ObjectAttributeErrors.
        """
        
        from jsonweb.decode import from_object, loader, ObjectAttributeError
                
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
        
        json_str = '{"__type__": "Person", "first_name": "shawn"}'
        with self.assertRaises(ObjectAttributeError) as context:
            person = loader(json_str)
            
        exc = context.exception
        
        self.assertEqual(exc.extras["attribute"], "last_name")
        self.assertEqual(str(exc), "Missing last_name attribute for Person.")
        
    def test_supplied_handler_dict(self):
        """
        Test that supplied ``handlers`` dict decodes objects.
        """
        from jsonweb.decode import loader
        
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        def person_decoder(cls, obj):
            return cls(obj["first_name"], obj["last_name"])
                    
        handlers = {"Person": {"cls": Person, "handler": person_decoder}}
        
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams"}'    
        person = loader(json_str, handlers=handlers)
        self.assertTrue(isinstance(person, Person))        
        self.assertEqual(person.first_name, "shawn")
        self.assertEqual(person.last_name, "adams")
        
    def test_supplied_handler_dict_overrides_from_object(self):
        """
        Test that a class decorated with from_object can have its
        handler and schema overriden with a supplied dict to
        decode.object_hook
        """
        from jsonweb.decode import from_object, loader
        
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        did_run = []
        def person_decoder(cls, obj):
            did_run.append(True)
            return cls(obj["first_name"], obj["last_name"])
        
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams"}'   
        person = loader(json_str)
        self.assertTrue(isinstance(person, Person))
        
        handlers = {"Person": {"handler": person_decoder}}      
        person = loader(json_str, handlers=handlers)
        self.assertTrue(isinstance(person, Person))
        self.assertTrue(did_run)
        
    def test_supplied_type_with_as_type(self):
        """
        Test that specifying an explicit type with ``as_type``
        decodes a json string this is missing the ``__type__`` key.
        """
        from jsonweb.decode import from_object, loader
        
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        json_str = '{"first_name": "shawn", "last_name": "adams"}'
        self.assertTrue(isinstance(loader(json_str, as_type="Person"), Person))
        json_str = '''[
            {"first_name": "shawn", "last_name": "adams"},
            {"first_name": "luke", "last_name": "skywalker"}
        ]'''
        persons = loader(json_str, as_type="Person")
        self.assertTrue(isinstance(persons, list))
        self.assertEqual(len(persons), 2)
        self.assertTrue(isinstance(persons[0], Person))
        self.assertTrue(isinstance(persons[1], Person))  
  
    def test_supplied__type__trumps_as_type(self):
        """
        Test that the __type__ key trumps as_type
        """

        from jsonweb.decode import from_object, loader
        from jsonweb.decode import ObjectDecodeError
        
        @from_object()
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
            
        @from_object()
        class Alien(object):
            def __init__(self, planet, number_of_legs):
                self.planet = planet
                self.number_of_legs = number_of_legs
                
        json_str = '{"__type__": "Person", "first_name": "shawn", "last_name": "adams"}'
        self.assertTrue(isinstance(loader(json_str, as_type="Alien"), Person))
        
        json_str = '{"first_name": "shawn", "last_name": "adams"}'        
        with self.assertRaises(ObjectDecodeError):
            loader(json_str, as_type="Alien")

                        
    def test_configured_object_hook_closure(self):
        """
        Test that we can configure a "custom" object_hook callable.
        """
        
        from jsonweb.decode import object_hook
        
        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name
                
        did_run = []
        def person_decoder(cls, obj):
            did_run.append(True)
            return cls(obj["first_name"], obj["last_name"])
        
        custom_object_hook = object_hook(
            handlers={"Person": {"handler": person_decoder, "cls": Person}},
            as_type="Person"
        )
        
        json_str = '{"first_name": "shawn", "last_name": "adams"}'
        person = json.loads(json_str, object_hook=custom_object_hook)
        self.assertTrue(isinstance(person, Person))
        self.assertEqual(did_run, [True])
        
        person = json.loads(json_str, object_hook=custom_object_hook)        
        self.assertEqual(did_run, [True, True])    
    