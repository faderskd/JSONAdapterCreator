import unittest
from copy import deepcopy

import base
import mixture
import errors


class ExampleAdapterForAdapterAttributeTests(base.BaseAdapter):
    required_attr = base.AdapterAttribute(data_type=str)
    not_required_attr = base.AdapterAttribute(data_type=str, required=False)
    required_with_not_required_attr = base.AdapterAttribute(data_type=str, required=False, required_with=['not_required_attr'])
    not_editable_attr = base.AdapterAttribute(data_type=dict, editable=False)


example_adapter_for_adapter_attribute_tests_data = {
    'required_attr': 'required attr value',
    'not_required_attr': 'not required attr value',
    'required_with_not_required_attr': 'required with not required attr',
    'not_editable_attr': {}
}


class AdapterAttributeTests(unittest.TestCase):
    def setUp(self):
        self.raw_data = deepcopy(example_adapter_for_adapter_attribute_tests_data)
        self.adapter = ExampleAdapterForAdapterAttributeTests(self.raw_data)

    def test_validation_not_throw_errors_for_proper_data(self):
        self.adapter.validate()

    def test_validation_throw_errors_for_missing_required_key(self):
        del self.raw_data['required_attr']
        with self.assertRaises(errors.AdapterValidationError):
            self.adapter.validate()

    def test_validation_throw_errors_for_missing_required_with_attr(self):
        del self.raw_data['not_required_attr']
        with self.assertRaises(errors.AdapterValidationError):
            self.adapter.validate()

    def test_validatation_throw_errors_for_improper_data_type(self):
        self.raw_data['required_attr'] = 2
        with self.assertRaises(errors.AdapterValidationError):
            self.adapter.validate()

    def test_getting_attribute_throw_errors_for_missing_key(self):
        del self.raw_data['required_attr']
        with self.assertRaises(errors.AdapterValidationError):
            self.adapter.required_attr

    def test_setting_not_editable_attribute_thor_error(self):
        with self.assertRaises(errors.AdapterValidationError):
            self.adapter.not_editable_attr = {}

    def test_getting_attribute_returns_proper_data(self):
        self.assertEqual(self.adapter.required_attr, 'required attr value')


class CompoundedField(mixture.AdapterCompounded):
    pass


class ExampleAdapterForBaseAdapterTests(base.BaseAdapter):
    simple_field = base.AdapterAttribute(str)
    # compounded_field =

if __name__ == '__main__':
    unittest.main()