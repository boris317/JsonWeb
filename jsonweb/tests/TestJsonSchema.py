import unittest
from jsonweb import dumper


class TestJsonSchema(unittest.TestCase):
    def test_non_nested_obj_schema(self):
        from jsonweb.schema import ObjectSchema
        from jsonweb.schema.validators import String, Float, Integer

        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String()
            id = Integer()
            test = Float()

        obj = {"first_name": "Shawn", "last_name": "Adams", "id": 1, "test": 12.0}
        self.assertEqual(obj, PersonSchema().validate(obj))

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
            }
        }

        self.assertEqual(obj, PersonSchema().validate(obj))

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

        with self.assertRaises(ValidationError) as c:
            schema.validate(obj)

        exc = c.exception
        self.assertEqual(3, len(exc.errors))
        self.assertTrue("last_name" in exc.errors)
        self.assertTrue("id" in exc.errors)
        self.assertTrue("test" in exc.errors)

        self.assertEqual("Missing required parameter.", str(exc.errors["last_name"]))
        self.assertEqual("Missing required parameter.", str(exc.errors["id"]))
        self.assertEqual("Missing required parameter.", str(exc.errors["test"]))

        obj = {"first_name": 10, "last_name": "Adams", "id": 1, "test": "bad type"}
        with self.assertRaises(ValidationError) as c:
            schema.validate(obj)

        exc = c.exception
        self.assertEqual(2, len(exc.errors))
        self.assertTrue("first_name" in exc.errors)
        self.assertTrue("test" in exc.errors)

        self.assertEqual("Expected str got int instead.", str(exc.errors["first_name"]))
        self.assertEqual("Expected float got str instead.", str(exc.errors["test"]))

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

        with self.assertRaises(ValidationError) as c:
            schema.validate(obj)

        exc = c.exception
        self.assertTrue("job" in exc.errors)
        self.assertEqual(len(exc.errors["job"].errors), 2)
        self.assertEqual(str(exc.errors["job"].errors["id"]), "Missing required parameter.")
        self.assertEqual(str(exc.errors["job"].errors["title"]), "Missing required parameter.")

    def test_list_schema_error(self):
        from jsonweb.schema import ObjectSchema, ValidationError
        from jsonweb.schema.validators import List, String

        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String()

        persons = [{"first_name": "shawn", "last_name": "adams"}, {"first_name": "luke"}]
        with self.assertRaises(ValidationError) as c:
            List(PersonSchema()).validate(persons)

        exc = c.exception
        self.assertEqual(1, exc.errors[0].extras["index"])

    def test_ensuretype_raises_validation_error(self):
        from jsonweb.schema import ObjectSchema, ValidationError
        from jsonweb.schema.validators import EnsureType, String

        class Foo(object):
            pass

        class JobSchema(ObjectSchema):
            title = String()
            id = EnsureType(Foo)

        with self.assertRaises(ValidationError) as c:
            JobSchema().validate({"title": "jedi", "id": 1})

        exc = c.exception
        self.assertEqual(str(exc.errors["id"]), "Expected Foo got int instead.")

    def test_ensuretype_kw_arguments_stick_around(self):
        """
        Tests bug fix for: http://github.com/boris317/JsonWeb/issues/7
        """
        from jsonweb.schema import ObjectSchema, validators as v
        from jsonweb import from_object

        class FooSchema(ObjectSchema):
            bar = v.EnsureType("Bar", optional=True, nullable=True)

        @from_object()
        class Bar(object):
            def __init__(self, honk):
                self.honk = honk

        ensure_type = FooSchema().bar

        self.assertTrue(ensure_type.nullable)
        self.assertFalse(ensure_type.required)

    def test_attributes_can_be_optional(self):
        from jsonweb.schema import ObjectSchema
        from jsonweb.schema.validators import String

        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String(optional=True)

        person = {"first_name": "shawn"}
        self.assertEqual(person, PersonSchema().validate(person))

    def test_attributes_can_have_default_values(self):
        from jsonweb.schema import ObjectSchema
        from jsonweb.schema.validators import String

        class PersonSchema(ObjectSchema):
            species = String(default="Human")
            first_name = String()
            last_name = String()

        person = PersonSchema().validate(
            {"first_name": "shawn", "last_name": "adams"}
        )
        self.assertEqual(person.get("species"), "Human")


class TestEachValidator(unittest.TestCase):
    def test_string_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import String

        v = String()
        self.assertEqual("foo", v.validate("foo"))
        with self.assertRaises(ValidationError) as c:
            v.validate(1)

        self.assertEqual("Expected str got int instead.", str(c.exception))

    def test_string_validator_max_len_kw(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import String

        v = String(max_len=3)
        self.assertEqual("foo", v.validate("foo"))
        with self.assertRaises(ValidationError) as c:
            v.validate("foobar")

        self.assertEqual("String exceeds max length of 3.", str(c.exception))

    def test_string_validator_min_len_kw(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import String

        v = String(min_len=3)

        with self.assertRaises(ValidationError) as c:
            v.validate("fo")

        self.assertEqual("String must be at least length 3.", str(c.exception))

    def test_regex_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Regex

        v = Regex(r"^foo[0-9]", max_len=10)
        self.assertEqual("foo12", v.validate("foo12"))

        with self.assertRaises(ValidationError) as c:
            v.validate("foo")

        exc = c.exception
        self.assertEqual("String does not match pattern '^foo[0-9]'.", str(exc))
        self.assertEqual("invalid_str", exc.extras["error_type"])

        with self.assertRaises(ValidationError) as c:
            v.validate("a"*11)
        self.assertEqual("String exceeds max length of 10.", str(c.exception))

    def test_integer_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Integer

        v = Integer()
        self.assertEqual(v.validate(42), 42)
        with self.assertRaises(ValidationError) as c:
            v.validate("foo")

        self.assertEqual("Expected int got str instead.", str(c.exception))

    def test_float_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Float

        v = Float()
        self.assertEqual(42.0, v.validate(42.0))
        with self.assertRaises(ValidationError) as c:
            v.validate(42)

        self.assertEqual("Expected float got int instead.", str(c.exception))

    def test_boolean_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Boolean

        v = Boolean()
        self.assertEqual(True, v.validate(True))
        with self.assertRaises(ValidationError) as c:
            v.validate("5")

        self.assertEqual("Expected bool got str instead.", str(c.exception))

    def test_number_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Number

        v = Number()
        self.assertEqual(42.0, v.validate(42.0))
        self.assertEqual(42, v.validate(42))
        with self.assertRaises(ValidationError) as c:
            v.validate("foo")

        self.assertEqual("Expected number got str instead.", str(c.exception))

    def test_dict_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Dict, Number

        v = Dict(Number)
        dict_to_test = {"foo": 1, "bar": 1.2}
        self.assertDictEqual(v.validate(dict_to_test), dict_to_test)

        with self.assertRaises(ValidationError) as c:
            v.validate({"foo": []})

        exc = c.exception
        self.assertEqual("Error validating dict.", str(exc))
        self.assertEqual(1, len(exc.errors))
        self.assertEqual("Expected number got list instead.", str(exc.errors["foo"]))
        self.assertEqual("invalid_dict", str(exc.extras["error_type"]))

    def test_dict_key_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Dict, Number, Regex

        v = Dict(Number, key_validator=Regex("[a-z]{2}_[A-Z]{2}"))
        dict_to_test = {"en_US": 1}
        self.assertDictEqual(v.validate(dict_to_test), dict_to_test)

        with self.assertRaises(ValidationError) as c:
            v.validate({"en-US": "1"})

        exc = c.exception
        self.assertEqual("String does not match pattern "
                         "'[a-z]{2}_[A-Z]{2}'.", str(exc.errors["en-US"]))
        self.assertEqual("invalid_dict_key", exc.errors["en-US"].extras["error_type"])

    def test_list_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import Number, List

        v = List(Number)
        self.assertEqual([1, 2, 3], v.validate([1, 2, 3]))

        with self.assertRaises(ValidationError) as c:
            v.validate("foo")

        self.assertEqual("Expected list got str instead.", str(c.exception))

        with self.assertRaises(ValidationError) as c:
            v.validate(["foo"])

        exc = c.exception
        self.assertEqual("Error validating list.", str(exc))
        self.assertEqual(1, len(exc.errors))
        self.assertEqual(0, exc.errors[0].extras["index"])
        self.assertEqual("invalid_list_item", exc.errors[0].extras["error_type"])
        self.assertEqual("Expected number got str instead.", str(exc.errors[0]))

    def test_ensuretype_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import EnsureType

        v = EnsureType((int, float))
        self.assertEqual(42.0, v.validate(42.0))
        self.assertEqual(42, v.validate(42))

        with self.assertRaises(ValidationError) as c:
            v.validate("foo")

        exc = c.exception
        self.assertEqual("Expected one of (int, float) got str instead.", str(exc))
        self.assertEqual("invalid_type", exc.extras["error_type"])

    def test_datetime_validator(self):
        from datetime import datetime
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import DateTime

        v = DateTime()
        self.assertIsInstance(v.validate("2012-01-01 12:30:00"), datetime)

        with self.assertRaises(ValidationError) as c:
            v.validate("01-01-2012")

        exc = c.exception
        self.assertEqual("time data '01-01-2012' does not "
                         "match format '%Y-%m-%d %H:%M:%S'", str(exc))
        self.assertEqual("invalid_datetime", exc.extras["error_type"])

    def test_nullable_is_true(self):
        from jsonweb.schema.validators import Integer

        v = Integer(nullable=True)
        self.assertEqual(None, v.validate(None))

    def test_one_of_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import OneOf

        self.assertEqual(OneOf(1, 2, 3).validate(1), 1)

        with self.assertRaises(ValidationError) as c:
            OneOf(1, "2", 3).validate("1")
            
        exc = c.exception
        self.assertEqual("Expected one of (1, '2', 3) "
                         "but got '1' instead.", str(exc))
        self.assertEqual("not_one_of", exc.extras["error_type"])

    def test_sub_set_of_validator(self):
        from jsonweb.schema import ValidationError
        from jsonweb.schema.validators import SubSetOf

        self.assertEqual(SubSetOf([1, 2, 3]).validate([1, 3]), [1, 3])

        with self.assertRaises(ValidationError) as c:
            SubSetOf([1, 2, 3]).validate([2, 5])

        exc = c.exception
        self.assertEqual("[2, 5] is not a subset of [1, 2, 3]", str(exc))
        self.assertEqual("not_a_sub_set_of", exc.extras["error_type"])


class TestValidationError(unittest.TestCase):

    def test_to_json_with_errors(self):
        from jsonweb.schema import ValidationError
        e = ValidationError("Boom", {"key": "value"})

        expected_dict = {"reason": "Boom", "errors": {"key": "value"}}
        self.assertDictEqual(e.to_json(), expected_dict)

    def test_to_json_with_no_errors(self):
        from jsonweb.schema import ValidationError
        e = ValidationError("Boom")

        self.assertEqual(e.to_json(), {"reason": "Boom"})

    def test_to_json_with_extras(self):
        from jsonweb.schema import ValidationError
        e = ValidationError("Boom", {"key": "value"}, foo="bar")

        expected_dict = {
            "reason": "Boom",
            "foo": "bar",
            "errors": {"key": "value"}
        }

        self.assertDictEqual(e.to_json(), expected_dict)
