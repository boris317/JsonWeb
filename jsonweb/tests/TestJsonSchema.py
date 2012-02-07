import unittest

class TestJsonSchema(unittest.TestCase):
    def test_non_nested_obj_schema(self):
        from jsonweb.schema import ObjectSchema, ValidationError
        from jsonweb.schema.validators import String, Float, Integer
        
        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String()
            id = Integer()
            test = Float()
            
        obj = {"first_name": "Shawn", "last_name": "Adams", "id": 1, "test": 12.0}
        self.assertEqual(PersonSchema().validate(obj), obj)
        
    def test_nested_schema(self):
        from jsonweb.schema import ObjectSchema
        from jsonweb.schema.validators import String, Float, Integer        
        
        class JobSchema(ObjectSchema):
            title = String()
            id = Integer()        
        
        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String()
            id = Integer()
            test = Float()
            job = JobSchema()
            
        obj = {
            "first_name": "Shawn",
            "last_name": "Adams", 
            "id": 1, 
            "test": 12.0, 
            "job": {
                "title": "zoo keeper", 
                "id": 1
        }}
            
        self.assertEqual(PersonSchema().validate(obj), obj)
        
    def test_raises_validation_error(self):
        from jsonweb.schema import ObjectSchema, ValidationError
        from jsonweb.schema.validators import String, Float, Integer
                    
        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String()
            id = Integer()
            test = Float()
            
        schema = PersonSchema()
        obj = {"first_name": "shawn"}
                
        with self.assertRaises(ValidationError) as context:
            schema.validate(obj)
            
        exc = context.exception
        self.assertEqual(len(exc.errors), 3)
        self.assertTrue("last_name" in exc.errors)
        self.assertTrue("id" in exc.errors)
        self.assertTrue("test" in exc.errors)
        
        self.assertEqual(exc.errors["last_name"].message, "Missing required parameter.")
        self.assertEqual(exc.errors["id"].message, "Missing required parameter.")
        self.assertEqual(exc.errors["test"].message, "Missing required parameter.")  
        
        obj = {"first_name": 10, "last_name": "Adams", "id": 1, "test": "bad type"}
        with self.assertRaises(ValidationError) as context:
            schema.validate(obj)
            
        exc = context.exception
        self.assertEqual(len(exc.errors), 2)
        self.assertTrue("first_name" in exc.errors)
        self.assertTrue("test" in exc.errors)
        
        self.assertEqual(exc.errors["first_name"].message, "Expected string got int instead.")
        self.assertEqual(exc.errors["test"].message, "Expected float got str instead.")
        
    def test_compound_error(self):
        """
        Test a nested schema raises a compound (nested) ValidationError.
        """
        from jsonweb.schema import ObjectSchema, ValidationError
        from jsonweb.schema.validators import String, Float, Integer
        
        class JobSchema(ObjectSchema):
            title = String()
            id = Integer()        
        
        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String()
            id = Integer()
            test = Float()
            job = JobSchema()
            
        schema = PersonSchema()
        
        obj = {
            "first_name": "Shawn",
            "last_name": "Adams", 
            "id": 1, 
            "test": 12.0, 
            "job": {}
        }
        
        with self.assertRaises(ValidationError) as context:
            schema.validate(obj)
            
        exc = context.exception
        self.assertTrue("job" in exc.errors)
        self.assertEqual(len(exc.errors["job"].errors), 2)
        self.assertEqual(exc.errors["job"].errors["id"].message, "Missing required parameter.")
        self.assertEqual(exc.errors["job"].errors["title"].message, "Missing required parameter.")        
        
    def test_list_schema_error(self):
        from jsonweb.schema import ObjectSchema, ValidationError
        from jsonweb.schema.validators import List, String
        
        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String()
            
        persons = [{"first_name": "shawn", "last_name": "adams"}, {"first_name": "luke"}]
        with self.assertRaises(ValidationError) as context:
            List(PersonSchema()).validate(persons)
            
        exc = context.exception
        self.assertEqual(exc.errors[0].error_index, 1)
        
    def test_ensuretype_raises_validation_error(self):
        from jsonweb.schema import ObjectSchema, ValidationError
        from jsonweb.schema.validators import EnsureType, String
        
        class Foo(object):
            pass
        
        class JobSchema(ObjectSchema):
            title = String()
            id = EnsureType(Foo)  
                    
        with self.assertRaises(ValidationError) as context:
            self.assertEqual(JobSchema().validate({"title": "jedi", "id": 1}), obj)
            
        exc = context.exception
        self.assertEqual(exc.errors["id"].message, "Expected Foo got int instead.")
            