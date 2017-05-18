import unittest
from copy import deepcopy

import tests.utils
import errors


class TestValidatorWithSimpleSchemaAttributes(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_user_data)
        self.user_schema = tests.utils.UserSchema()
        self.validator = self.user_schema.get_validator()

    def test_validator_not_throw_errors_for_proper_data(self):
        self.validator.validate(self.user_data)

    def test_validator_thor_errors_for_incorrect_root_data_type(self):
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(2)

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


class TestValidatorWithCompoundedSchemaAttributes(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_compounded_user_data)
        self.user_schema = tests.utils.UserCompoundedSchema()
        self.validator = self.user_schema.get_validator()

    def test_validator_not_throw_errors_for_proper_data(self):
        self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_main_data_type(self):
        self.user_data['profile'] = []
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_nested_data_type(self):
        self.user_data['profile']['last_logged'] = 2
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_deeply_nested_data_type(self):
        self.user_data['profile']['settings']['stay_logged'] = 'yes'
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_missing_nested_data(self):
        del self.user_data['profile']['settings']
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)


class TestValidatorFreeContentWithCompoundedSchemaAttributes(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_free_content_user_data)
        self.user_schema = tests.utils.UserWithFreeContentAttributesSchema()
        self.validator = self.user_schema.get_validator()

    def test_validator_not_throw_errors_for_proper_data(self):
        self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_main_data_type(self):
        self.user_data['attributes'] = 4
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_missing_main_key(self):
        del self.user_data['attributes']
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_simple_mapping_type(self):
        self.user_data['attributes']['surname'] = 2
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_compound_mapping_type(self):
        self.user_data['attributes']['appearance'] = []
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_missing_deeply_nested_keys(self):
        del self.user_data['attributes']['appearance']['age']
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)


class TestValidatorWithFreeTypeSchemaAttributes(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_free_type_user_data)
        self.user_schema = tests.utils.UserWithFreeTypeAttributeSchema()
        self.validator = self.user_schema.get_validator()

    def test_validator_not_throw_errors_for_proper_data(self):
        self.validator.validate(self.user_data)
        self.user_data['attributes'] = 'no description'
        self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_main_data_type(self):
        self.user_data['attributes'] = 4
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_missing_main_key(self):
        del self.user_data['attributes']
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_missing_nested_data(self):
        del self.user_data['attributes']['appearance']['height']
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_nested_data_type(self):
        self.user_data['attributes']['appearance']['height'] = 2
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_empty_nested_data(self):
        self.user_data['attributes']['surname'] = ''
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)


class TestValidatorWithCollectionSchemaAttributes(unittest.TestCase):
    def setUp(self):
        self.user_data = deepcopy(tests.utils.example_collection_user_data)
        self.user_schema = tests.utils.UserWithCollectionAttributeSchema()
        self.validator = self.user_schema.get_validator()

    def test_validator_not_throw_errors_for_proper_data(self):
        self.validator.validate(self.user_data)

    def test_validator_throw_error_for_missing_main_key(self):
        del self.user_data['posts']
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_missing_nested_key(self):
        del self.user_data['posts'][0]['title']
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_nested_data_type(self):
        self.user_data['posts'][1]['tags'] = 123
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)

    def test_validator_throw_error_for_incorrect_collection_type(self):
        self.user_data['posts'][1] = 'hello'
        with self.assertRaises(errors.AdapterValidationError):
            self.validator.validate(self.user_data)
