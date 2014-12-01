import unittest
from jsonweb import from_object
from jsonweb.schema import ObjectSchema, SchemaMeta
from jsonweb.validators import String, Float, Integer, ValidationError, List, \
    EnsureType


class TestSchema(unittest.TestCase):
    def test_non_nested_obj_schema(self):

        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String()
            id = Integer()
            test = Float()

        obj = {"first_name": "Shawn", "last_name": "Adams", "id": 1, "test": 12.0}
        self.assertEqual(obj, PersonSchema().validate(obj))

    def test_nested_schema(self):

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

        self.assertEqual("Missing required parameter.",
                         str(exc.errors["last_name"]))

        self.assertEqual("Missing required parameter.",
                         str(exc.errors["id"]))

        self.assertEqual("Missing required parameter.",
                         str(exc.errors["test"]))

        obj = {
            "id": 1,
            "first_name": 10,
            "last_name": "Adams",
            "test": "bad type"
        }

        with self.assertRaises(ValidationError) as c:
            schema.validate(obj)

        exc = c.exception
        self.assertEqual(2, len(exc.errors))
        self.assertTrue("first_name" in exc.errors)
        self.assertTrue("test" in exc.errors)

        self.assertEqual("Expected str got int instead.",
                         str(exc.errors["first_name"]))

        self.assertEqual("Expected float got str instead.",
                         str(exc.errors["test"]))

    def test_compound_error(self):
        """
        Test a nested schema raises a compound (nested) ValidationError.
        """

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
        self.assertEqual(str(exc.errors["job"].errors["id"]),
                         "Missing required parameter.")

        self.assertEqual(str(exc.errors["job"].errors["title"]),
                         "Missing required parameter.")

    def test_list_schema_error(self):

        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String()

        persons = [
            {
               "first_name": "shawn",
               "last_name": "adams"
            },
            {
                "first_name": "luke"
            }
        ]

        with self.assertRaises(ValidationError) as c:
            List(PersonSchema()).validate(persons)

        exc = c.exception
        self.assertEqual(1, exc.errors[0].extras["index"])

    def test_EnsureType_raises_validation_error(self):

        class Foo(object):
            pass

        class JobSchema(ObjectSchema):
            title = String()
            id = EnsureType(Foo)

        with self.assertRaises(ValidationError) as c:
            JobSchema().validate({"title": "jedi", "id": 1})

        exc = c.exception
        self.assertEqual(str(exc.errors["id"]), "Expected Foo got int instead.")

    def test_EnsureType_kw_arguments_stick_around(self):
        """
        Tests bug fix for: http://github.com/boris317/JsonWeb/issues/7
        """

        class FooSchema(ObjectSchema):
            bar = EnsureType("Bar", optional=True, nullable=True)

        @from_object()
        class Bar(object):
            def __init__(self, honk):
                self.honk = honk

        ensure_type = FooSchema().bar

        self.assertTrue(ensure_type.nullable)
        self.assertFalse(ensure_type.required)

    def test_attributes_can_be_optional(self):

        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String(optional=True)

        person = {"first_name": "shawn"}
        self.assertEqual(person, PersonSchema().validate(person))

    def test_attributes_can_have_default_values(self):

        class PersonSchema(ObjectSchema):
            species = String(default="Human")
            first_name = String()
            last_name = String()

        person = PersonSchema().validate(
            {"first_name": "shawn", "last_name": "adams"}
        )
        self.assertEqual(person.get("species"), "Human")

    def test_create(self):
        schema_cls = ObjectSchema.create("MySchema", {
            "first-name": String(),
            "last-name": String(optional=True)
        })

        self.assertEqual(type(schema_cls), SchemaMeta)
        self.assertIsInstance(schema_cls(), ObjectSchema)

        with self.assertRaises(ValidationError) as c:
            schema_cls().validate({'first-name': 1})

        self.assertIn('first-name', c.exception.errors)

    def test_kw_args_are_passed_correctly(self):

        class PersonSchema(ObjectSchema):
            first_name = String()
            last_name = String(optional=True)

        schema = PersonSchema(default="foo", optional=True,
                              nullable=True, reason_code="BECAUSE")

        self.assertEqual("foo", schema.default)
        self.assertEqual("BECAUSE", schema.reason_code)
        self.assertTrue(schema.nullable)
        self.assertFalse(schema.required)

    def test_subclasses_inherit_validators_from_base_schema(self):

        class BaseSchema(ObjectSchema):
            foo = String()

        class BarSchema(BaseSchema):
            bar = String()

        schema = BarSchema()

        # assert _fields are merged
        self.assertIn("foo", schema._fields)
        self.assertIn("bar", schema._fields)

        with self.assertRaises(ValidationError) as c:
            schema.validate({})

        # assert validators run correctly
        exc = c.exception
        self.assertIn("foo", exc.errors)
        self.assertIn("bar", exc.errors)
