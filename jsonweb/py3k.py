"""
Code needed to support python 3. :func:`items` is a slightly modified version
of ``six.iteritems`` `six <https://pythonhosted.org/six/#six.iteritems>`_
"""

import sys

PY3k = sys.version_info[0] == 3

if PY3k:
    basestring = (str, bytes)
    _iteritems = "items"
else:
    basestring = basestring
    _iteritems = "iteritems"


def items(d):
    return getattr(d, _iteritems)()