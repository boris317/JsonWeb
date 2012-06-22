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
        
        self.assertEqual(exc.errors["first_name"].message, "Expected str got int instead.")
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
        
    def test_attributes_can_be_optional(self):
        from jsonweb.schema import ObjectSchema, ValidationError
        from jsonweb.schema.validators import EnsureType, String
        
        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String(optional=True)
            
        person = {"first_name": "shawn"}
        self.assertEqual(PersonSchema().validate(person), person)

class TestEachValidator(unittest.TestCase):
    def test_string_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import String
        
        v = String()
        self.assertEqual(v.validate("foo"), "foo")
        with self.assertRaises(ValidationError) as context:
            v.validate(1)
            
        exception = context.exception
        self.assertEqual("Expected str got int instead.", str(exception))
        
    def test_integer_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Integer
        
        v = Integer()
        self.assertEqual(v.validate(42), 42)
        with self.assertRaises(ValidationError) as context:
            v.validate("foo")
            
        exception = context.exception
        self.assertEqual("Expected int got str instead.", str(exception))
        
    def test_float_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Float
        
        v = Float()
        self.assertEqual(v.validate(42.0), 42.0)
        with self.assertRaises(ValidationError) as context:
            v.validate(42)
            
        exception = context.exception
        self.assertEqual("Expected float got int instead.", str(exception))
        
    def test_number_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Number
        
        v = Number()
        self.assertEqual(v.validate(42.0), 42.0)
        self.assertEqual(v.validate(42), 42)
        with self.assertRaises(ValidationError) as context:
            v.validate("foo")
            
        exception = context.exception
        self.assertEqual("Expected number got str instead.", str(exception))
        
    def test_list_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Number, List
        
        v = List(Number)
        self.assertEqual(v.validate([1,2,3]), [1,2,3])
        
        with self.assertRaises(ValidationError) as context:
            v.validate("foo")
            
        exception = context.exception
        self.assertEqual("Expected list got str instead.", str(exception))
        
        with self.assertRaises(ValidationError) as context:
            v.validate(["foo"])
            
        exception = context.exception
        self.assertEqual("Error validating list.", str(exception))
        self.assertEqual(len(exception.errors), 1)
        self.assertEqual(exception.errors[0].error_index, 0)
        self.assertEqual(str(exception.errors[0]), "Expected number got str instead.")  
        
    def test_ensuretype_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import EnsureType
        
        v = EnsureType((int, float))
        self.assertEqual(v.validate(42.0), 42.0)
        self.assertEqual(v.validate(42), 42)
        
        with self.assertRaises(ValidationError) as context:
            v.validate("foo")
            
        exception = context.exception
        self.assertEqual("Expected one of (int, float) got str instead.", str(exception))
        
    def test_datetime_validator(self):
        from datetime import datetime
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import DateTime
   
        v = DateTime()
        self.assertIsInstance(v.validate("2012-01-01 12:30:00"), datetime)
        
        with self.assertRaises(ValidationError) as context:
            v.validate("01-01-2012")
            
        exception = context.exception
        self.assertEqual("time data '01-01-2012' does not match format '%Y-%m-%d %H:%M:%S'", str(exception))        