JsonWeb Changelog
=================

Version 0.8
-------------

-- Added :class:`~jsonweb.validators.Dict`
-- Added ``default`` kw arg to validators
-- Added ``reason_code`` to :class:`~jsonweb.validators.ValidationError`
-- Refactored the ``jsonweb.schema`` package into `~jsonweb.validators` and
   `~jsonweb.schema` modules. (Breaks backwards compatibility)


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
