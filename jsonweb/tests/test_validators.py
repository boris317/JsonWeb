import unittest
from datetime import datetime

from jsonweb.validators import Dict, List, String, Regex, Integer, Float, \
    Number, OneOf, SubSetOf, DateTime, Boolean, EnsureType, ValidationError


class TestEachValidator(unittest.TestCase):
    def test_string_validator(self):
        v = String()
        self.assertEqual("foo", v.validate("foo"))
        with self.assertRaises(ValidationError) as c:
            v.validate(1)

        self.assertEqual("Expected str got int instead.", str(c.exception))

    def test_string_validator_max_len_kw(self):
        v = String(max_len=3)
        self.assertEqual("foo", v.validate("foo"))
        with self.assertRaises(ValidationError) as c:
            v.validate("foobar")

        self.assertEqual("String exceeds max length of 3.", str(c.exception))

    def test_string_validator_min_len_kw(self):
        v = String(min_len=3)

        with self.assertRaises(ValidationError) as c:
            v.validate("fo")

        self.assertEqual("String must be at least length 3.", str(c.exception))

    def test_regex_validator(self):
        v = Regex(r"^foo[0-9]", max_len=10)
        self.assertEqual("foo12", v.validate("foo12"))

        with self.assertRaises(ValidationError) as c:
            v.validate("foo")

        exc = c.exception
        self.assertEqual("String does not match pattern '^foo[0-9]'.", str(exc))
        self.assertEqual("invalid_str", exc.reason_code)

        with self.assertRaises(ValidationError) as c:
            v.validate("a"*11)
        self.assertEqual("String exceeds max length of 10.", str(c.exception))

    def test_integer_validator(self):
        v = Integer()
        self.assertEqual(v.validate(42), 42)
        with self.assertRaises(ValidationError) as c:
            v.validate("foo")

        self.assertEqual("Expected int got str instead.", str(c.exception))

    def test_float_validator(self):
        v = Float()
        self.assertEqual(42.0, v.validate(42.0))
        with self.assertRaises(ValidationError) as c:
            v.validate(42)

        self.assertEqual("Expected float got int instead.", str(c.exception))

    def test_boolean_validator(self):
        v = Boolean()
        self.assertEqual(True, v.validate(True))
        with self.assertRaises(ValidationError) as c:
            v.validate("5")

        self.assertEqual("Expected bool got str instead.", str(c.exception))

    def test_number_validator(self):
        v = Number()
        self.assertEqual(42.0, v.validate(42.0))
        self.assertEqual(42, v.validate(42))
        with self.assertRaises(ValidationError) as c:
            v.validate("foo")

        self.assertEqual("Expected number got str instead.", str(c.exception))

    def test_dict_validator(self):
        v = Dict(Number)
        dict_to_test = {"foo": 1, "bar": 1.2}
        self.assertDictEqual(v.validate(dict_to_test), dict_to_test)

        with self.assertRaises(ValidationError) as c:
            v.validate({"foo": []})

        exc = c.exception
        self.assertEqual("Error validating dict.", str(exc))
        self.assertEqual(1, len(exc.errors))
        self.assertEqual("Expected number got list instead.", str(exc.errors["foo"]))
        self.assertEqual("invalid_dict", exc.reason_code)

    def test_dict_key_validator(self):
        v = Dict(Number, key_validator=Regex("[a-z]{2}_[A-Z]{2}"))
        dict_to_test = {"en_US": 1}
        self.assertDictEqual(v.validate(dict_to_test), dict_to_test)

        with self.assertRaises(ValidationError) as c:
            v.validate({"en-US": "1"})

        exc = c.exception
        self.assertEqual("String does not match pattern "
                         "'[a-z]{2}_[A-Z]{2}'.", str(exc.errors["en-US"]))
        self.assertEqual("invalid_dict_key", exc.errors["en-US"].reason_code)

    def test_list_validator(self):
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
        self.assertEqual("invalid_list_item", exc.errors[0].reason_code)
        self.assertEqual("Expected number got str instead.", str(exc.errors[0]))

    def test_ensuretype_validator(self):
        v = EnsureType((int, float))
        self.assertEqual(42.0, v.validate(42.0))
        self.assertEqual(42, v.validate(42))

        with self.assertRaises(ValidationError) as c:
            v.validate("foo")

        exc = c.exception
        self.assertEqual("Expected one of (int, float) got str instead.", str(exc))
        self.assertEqual("invalid_type", exc.reason_code)

    def test_datetime_validator(self):
        v = DateTime()
        self.assertIsInstance(v.validate("2012-01-01 12:30:00"), datetime)

        with self.assertRaises(ValidationError) as c:
            v.validate("01-01-2012")

        exc = c.exception
        self.assertEqual("time data '01-01-2012' does not "
                         "match format '%Y-%m-%d %H:%M:%S'", str(exc))
        self.assertEqual("invalid_datetime", exc.reason_code)

    def test_nullable_is_true(self):
        v = Integer(nullable=True)
        self.assertEqual(None, v.validate(None))

    def test_one_of_validator(self):
        self.assertEqual(OneOf(1, 2, 3).validate(1), 1)

        with self.assertRaises(ValidationError) as c:
            OneOf(1, "2", 3).validate("1")
            
        exc = c.exception
        self.assertEqual("Expected one of (1, '2', 3) "
                         "but got '1' instead.", str(exc))
        self.assertEqual("not_one_of", exc.reason_code)

    def test_sub_set_of_validator(self):
        self.assertEqual(SubSetOf([1, 2, 3]).validate([1, 3]), [1, 3])

        with self.assertRaises(ValidationError) as c:
            SubSetOf([1, 2, 3]).validate([2, 5])

        exc = c.exception
        self.assertEqual("[2, 5] is not a subset of [1, 2, 3]", str(exc))
        self.assertEqual("not_a_sub_set_of", exc.reason_code)


class TestValidationError(unittest.TestCase):

    def test_to_json_with_errors(self):
        e = ValidationError("Boom", errors={"key": "value"})

        expected_dict = {"reason": "Boom", "errors": {"key": "value"}}
        self.assertDictEqual(e.to_json(), expected_dict)

    def test_to_json_with_no_errors(self):
        e = ValidationError("Boom")

        self.assertEqual(e.to_json(), {"reason": "Boom"})

    def test_to_json_with_extras(self):
        e = ValidationError("Boom", errors={"key": "value"}, foo="bar")

        expected_dict = {
            "reason": "Boom",
            "foo": "bar",
            "errors": {"key": "value"}
        }

        self.assertDictEqual(e.to_json(), expected_dict)

    def test_to_json_with_reason_code(self):
        e = ValidationError("Boom", reason_code="because",
                            errors={"key": "value"}, foo="bar")

        expected_dict = {
            "reason": "Boom",
            "reason_code": "because",
            "foo": "bar",
            "errors": {"key": "value"}
        }

        self.assertDictEqual(e.to_json(), expected_dict)