import unittest
from copy import deepcopy

import base
import mixture
import errors
import pprint

pp = pprint.PrettyPrinter(indent=2)


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


class Address(mixture.AdapterObjectAttribute):
    street = base.AdapterAttribute(str, target_alias='user_street')
    postal_code = base.AdapterAttribute(str)


class Team(mixture.AdapterObjectAttribute):
    team_name = base.AdapterAttribute(str)


class Profile(mixture.AdapterObjectAttribute):
    is_active = base.AdapterAttribute(bool)
    id = base.AdapterAttribute(int, target_alias='user_id')
    team = Team(searchable=True, target_alias='user_team')


class AdditionalData(mixture.AdapterObjectAttribute):
    phone_number = base.AdapterAttribute(str)
    email = base.AdapterAttribute(str)


class User(base.BaseAdapter):
    def __init__(self, raw_data):
        super().__init__(raw_data, source_aliases=['user_id', 'user_street', 'user_team'])
    username = base.AdapterAttribute(str)
    address = Address(required=False, searchable=True)
    profile = Profile(searchable=True, insertable=True, insert_type=(bool, int))
    additional_data = AdditionalData(required=False, insertable=True, insert_type=str)


user_raw_data = {
    'username': 'Daniel',
    'address': {
        'street': 'Jana Pawla II',
        'postal_code': '05-222 New York'
    },
    'profile': {
        'is_active': True,
        'id': 123,
        'team': {
            'team_name': 'Kolka team'
        }
    }
}


class BaseAdapterTests(unittest.TestCase):
    def setUp(self):
        self.raw_data = deepcopy(user_raw_data)
        self.user = User(self.raw_data)

    def test_adapter_not_raises_errors_for_proper_data(self):
        self.user.validate()

    def test_compounded_object_return_proper_adapter_object(self):
        self.assertIsInstance(self.user.profile, base.BaseAdapter)
        self.assertIsInstance(self.user.profile.team, base.BaseAdapter)

    def test_attribute_of_returned_adapter_object_can_be_accessed_and_return_proper_values(self):
        self.assertEqual(self.user.profile.is_active, True)
        self.assertEqual(self.user.profile.id, 123)
        self.assertEqual(self.user.address.street, 'Jana Pawla II')
        self.assertEqual(self.user.profile.team.team_name, 'Kolka team')

    def test_profile_and_address_and_team_compounded_attributes_are_searchable(self):
        self.assertEqual(self.user.street, 'Jana Pawla II')
        self.assertEqual(self.user.postal_code, '05-222 New York')
        self.assertEqual(self.user.id, 123)
        self.assertIsInstance(self.user.team, base.BaseAdapter)
        self.assertEqual(self.user.team.team_name, 'Kolka team')
        self.assertEqual(self.user.team_name, 'Kolka team')

    def test_profile_and_additional_data_are_insertable(self):
        with self.assertRaises(errors.AdapterValidationError):
            self.user.email = 'daniel@op.pl'
        self.user.additional_data = {}
        self.user.email = 'daniel@op.pl'
        self.user.phone_number = '111-222-333'
        self.assertEqual(self.raw_data['additional_data']['email'], 'daniel@op.pl')
        self.assertEqual(self.raw_data['additional_data']['phone_number'], '111-222-333')

        self.user.is_active = False
        self.user.id = 444
        self.assertEqual(self.raw_data['profile']['is_active'], False)
        self.assertEqual(self.raw_data['profile']['id'], 444)

    def test_id_and_street_and_team_aliases_works_propertly(self):
        self.assertEqual(self.user.user_id, 123)
        self.assertEqual(self.user.user_street, 'Jana Pawla II')
        self.assertIsInstance(self.user.user_team, base.BaseAdapter)
        self.assertEqual(self.user.user_team.team_name, 'Kolka team')


ingredients_mapping = {
    str: base.AdapterAttribute(str),
    dict: mixture.AdapterObjectFreeContentAttribute({str: base.AdapterAttribute(str)})
}


class Ingredients(mixture.AdapterObjectFreeContentAttribute):
    unit = mixture.AdapterAttribute(str)


class Potion(base.BaseAdapter):
    name = base.AdapterAttribute(str)
    ingredients = Ingredients(ingredients_mapping, searchable=True)


potion_raw_data = {
    'name': 'elixir of youth',
    'ingredients': {
        'unit': 'ml',
        'water': '500 ml',
        'vinegar': {
            'old_wine': '15 ml',
            'alcohol': '10 ml'
        }
    }
}


class AdapterFreeContentTests(unittest.TestCase):
    def setUp(self):
        self.raw_data = deepcopy(potion_raw_data)
        self.potion = Potion(self.raw_data)

    def test_adapter_not_throw_errors_for_proper_data(self):
        self.potion.validate()

    def test_adapter_properly_fetch_data(self):
        self.assertEqual(self.potion.name, 'elixir of youth')
        self.assertIsInstance(self.potion.ingredients, mixture.AdapterFreeContent)
        self.assertEqual(self.potion.ingredients.unit, 'ml')
        self.assertEqual(self.potion.ingredients.vinegar.old_wine, '15 ml')

    def test_ingredients_are_searchable(self):
        self.assertEqual(self.potion.unit, 'ml')
        self.assertEqual(self.potion.water, '500 ml')
        self.assertIsInstance(self.potion.vinegar, mixture.AdapterFreeContent)
        self.assertEqual(self.potion.vinegar.old_wine, '15 ml')
        self.assertEqual(self.potion.vinegar.alcohol, '10 ml')

    def test_set_ingredients(self):
        self.potion.ingredients.salt = '1ml'
        self.potion.ingredients.cake = {
            'salt': 333
        }

if __name__ == '__main__':
    unittest.main()