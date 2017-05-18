import unittest
from copy import deepcopy

import tests.utils
import validators


class TestSchemaWithSimpleAttributes(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_user_data)
        self.user_schema = tests.utils.UserSchema()
        self.validator = self.user_schema.get_validator()

    def test_schema_properly_generates_validator_object(self):
        self.assertIsInstance(self.validator, validators.SchemaValidator)

    def test_schema_properly_generates_validator_child_objects(self):
        child_validators = self.validator._child_validators
        self.assertEqual(len(child_validators), 5)
        for v in child_validators:
            self.assertIsInstance(v, validators.AttributeValidator)


class TestSchemaWithCompoundedAttributes(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_compounded_user_data)
        self.user_schema = tests.utils.UserCompoundedSchema()
        self.validator = self.user_schema.get_validator()

    def test_schema_properly_generates_validator_object(self):
        self.assertIsInstance(self.validator, validators.SchemaValidator)

    def test_schema_properly_generates_validator_child_objects(self):
        compounded_validator = self.validator._child_validators[-1]
        self.assertIsInstance(compounded_validator, validators.CompoundedAttributeValidator)
        self.assertIsInstance(compounded_validator._child_validators[0], validators.AttributeValidator)
        self.assertIsInstance(compounded_validator._child_validators[1], validators.CompoundedAttributeValidator)
        self.assertIsInstance(compounded_validator._child_validators[1]._child_validators[0], validators.AttributeValidator)
        self.assertIsInstance(compounded_validator._child_validators[1]._child_validators[1], validators.AttributeValidator)


class TestSchemaFreeContentWithCompoundedAttributes(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_free_content_user_data)
        self.user_schema = tests.utils.UserWithFreeContentAttributesSchema()
        self.validator = self.user_schema.get_validator()

    def test_schema_properly_generates_validator_object(self):
        self.assertIsInstance(self.validator._child_validators[-1], validators.FreeContentCompoundedAttributeValidator)


class TestSchemaFreeTypeAttribute(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_free_type_user_data)
        self.user_schema = tests.utils.UserWithFreeTypeAttributeSchema()
        self.validator = self.user_schema.get_validator()

    def test_schema_properly_generates_validator_object(self):
        self.assertIsInstance(self.validator._child_validators[-1], validators.FreeTypeAttributeValidator)


