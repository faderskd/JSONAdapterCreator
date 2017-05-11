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