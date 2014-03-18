:mod:`jsonweb.schema`
======================================================

.. contents:: Table of Contents
   :depth: 3

.. automodule:: jsonweb.schema

ValidationErrors
----------------

.. autoclass:: ValidationError


Validators
-------------

.. automodule:: jsonweb.schema.validators

.. autoclass:: jsonweb.schema.base.BaseValidator
   :members:

   .. automethod:: __init__

.. autoclass:: jsonweb.schema.validators.String
.. autoclass:: jsonweb.schema.validators.Regex
.. autoclass:: jsonweb.schema.validators.Number
.. autoclass:: jsonweb.schema.validators.Integer
.. autoclass:: jsonweb.schema.validators.Float
.. autoclass:: jsonweb.schema.validators.Boolean
.. autoclass:: jsonweb.schema.validators.DateTime
.. autoclass:: jsonweb.schema.validators.EnsureType
.. autoclass:: jsonweb.schema.validators.List
.. autoclass:: jsonweb.schema.validators.OneOf
.. autoclass:: jsonweb.schema.validators.SubSetOf
