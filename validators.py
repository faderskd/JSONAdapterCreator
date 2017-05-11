from errors import AdapterValidationError


class AttributeValidator:
    def __init__(self, name, data_type, required, required_with):
        self._name = name
        self._data_type = data_type
        self._required = required
        self._required_with = required_with

    def get_name(self):
        return self._name

    def validate(self, parent_data):
        raw_value = self._get_raw_value_from_parent_data(parent_data)

        if self._required and raw_value is None:
            raise AdapterValidationError('Missing key "%s"' % self._name)

        if raw_value is not None and not isinstance(raw_value, self._data_type):
            raise AdapterValidationError('Incorrect data type for key "%s"' % self._name)

        if raw_value is None:
            return

        required_with = set(self._required_with)
        for k, _ in parent_data.items():
            if k in required_with:
                required_with.remove(k)
        if required_with:
            s = 'Attribute "%s" required together with "%s"' % (self._name, ", ".join([k for k in self._required_with]))
            raise AdapterValidationError(s)

    def _get_raw_value_from_parent_data(self, parent_data):
        return parent_data.get(self._name, None)


class CompoundAttributeValidator(AttributeValidator):
    def __init__(self, child_validators, **kwargs):
        super().__init__(data_type=dict, **kwargs)
        self._child_validators = child_validators

    def validate(self, parent_data):
        super().validate(parent_data)
        raw_value = self._get_raw_value_from_parent_data(parent_data)
        if raw_value is None:
            return
        for child_validator in self._child_validators:
            child_validator.validate(raw_value)


class SchemaValidator:
    def __init__(self, child_validators):
        self._child_validators = child_validators

    def validate(self, data):
        if type(data) != dict:
            raise AdapterValidationError('Incorrect root data type')
        for child_validator in self._child_validators:
            child_validator.validate(data)







class MappedValidatedAttribute:
    def __init__(self, data_type):
        self._data_type = data_type

    def validate(self, raw_value):
        pass


class MappingMixin(object):
    def __init__(self, mapping):
        super().__init__()
        self._mapping = mapping

    def get_attribute_inst(self, name, raw_value):
        self._validate_against_mapping(name, raw_value)


    def _validate_against_mapping(self, name, raw_value):
        if type(raw_value) not in self._mapping:
            raise AdapterValidationError('Data type for key "%s" not in types mapping' % name)


# class FreeContentCompoundValidatedAttribute(CompoundValidatedAttribute):
#     def __init__(self, mapping, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._mapping = mapping
#
#     def validate(self):
#         super().validate()
        # child_attribute_names = {c.name for c in self._child_attributes}
        # for k, v in self.