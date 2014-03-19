JsonWeb Changelog
=================

Version 0.8
-------------

-- Added :class:`~jsonweb.schema.validators.Dict`
-- Added `default` kw arg to validators
-- Added `error_type`` key to ``extras`` dict for validation errors raised
   by all validators. Which will show up in JSON serialization of the error.


Version 0.7.1
-------------

-- Fixed exception when calling ValidationError.to_json in python 3


Version 0.7.0
-------------

-- Python 3 support!


Version 0.6.6
-------------
- Added `min_len` kw arg to :class:`~jsonweb.schema.validators.String`


Version 0.6.5
-------------

- Renamed README to README.rst
- Renamed CHANGES to CHANGES.rst


Version 0.6.4
--------------

- Added :class:`~jsonweb.schema.validators.OneOf`
- Added :class:`~jsonweb.schema.validators.SubSetOf`
