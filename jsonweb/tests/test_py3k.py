import sys
import unittest


def major_version():
    return sys.version_info[0]


class TestPy3k(unittest.TestCase):

    def test_PY3K_is_set_correctly(self):
        from jsonweb.py3k import PY3k

        if major_version() == 3:
            self.assertTrue(PY3k)
        if major_version() == 2:
            self.assertFalse(PY3k)

    def test_basestring_is_set_correctly(self):
        from jsonweb.py3k import basestring as _basestring

        if major_version() == 3:
            self.assertEqual(_basestring, (str, bytes))
        if major_version() == 2:
            self.assertEqual(_basestring, basestring)

    def test_items(self):
        from jsonweb.py3k import items

        if major_version() == 3:
            self.assertEqual(type(items({})), type({}.items()))
        if major_version() == 2:
            self.assertEqual(type(items({})), type({}.iteritems()))
