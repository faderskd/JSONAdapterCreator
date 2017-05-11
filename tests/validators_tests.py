import unittest
from copy import deepcopy

import tests.utils
import errors


class TestValidatorForSimpleSchemaAttributes(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_user_data)
        self.user_schema = tests.utils.UserSchema()
        self.validator = self.user_schema.get_validator()

    def test_validator_not_throw_errors_for_proper_data(self):
        self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_data_type(self):
        self.user_data['username'] = {}
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_missing_required_key(self):
        del self.user_data['is_active']
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_missing_required_with_key(self):
        del self.user_data['birth_date']
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_not_throw_error_for_missing_not_required_key(self):
        del self.user_data['first_name']
        self.validator.validate(self.user_data)