from errors import AdapterValidationError, UnexpectedMappingElement


class AttributeValidator:
    def __init__(self, data_type, required, required_with, name=None):
        self._data_type = data_type
        self._required = required
        self._required_with = required_with
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def validate(self, parent_data, error_path=None):
        _, error_path_str = self._generate_error_path_pair(error_path)

        raw_value = self._get_raw_value_from_parent_data(parent_data)
        if self._required and raw_value is None:
            raise AdapterValidationError('Missing key "%s"' % error_path_str)

        if raw_value is not None and not isinstance(raw_value, self._data_type):
            raise AdapterValidationError('Incorrect data type for key "%s"' % error_path_str)

        if self._required and not raw_value:
            raise AdapterValidationError('Empty value for key "%s"' % error_path_str)

        if raw_value is None:
            return

        required_with = set(self._required_with)
        for k, _ in parent_data.items():
            if k in required_with:
                required_with.remove(k)
        if required_with:
            s = 'Attribute "%s" required together with "%s"' % (error_path_str, ", ".join([k for k in self._required_with]))
            raise AdapterValidationError(s)

    def _get_raw_value_from_parent_data(self, parent_data):
        return parent_data.get(self._name, None)

    def _generate_error_path_pair(self, error_path=None):
        if not error_path:
            error_path = []
        error_path_str = "/".join(error_path) + "/" + self._name
        error_path = error_path + [self.name]
        return error_path, error_path_str


class CompoundedAttributeValidator(AttributeValidator):
    def __init__(self, child_validators, **kwargs):
        kwargs.pop('data_type', None)
        super().__init__(data_type=dict, **kwargs)
        self._child_validators = child_validators

    def validate(self, parent_data, error_path=None):
        super().validate(parent_data, error_path)
        error_path, _ = self._generate_error_path_pair(error_path)

        raw_value = self._get_raw_value_from_parent_data(parent_data)
        if raw_value is None:
            return
        for child_validator in self._child_validators:
            child_validator.validate(raw_value, error_path)


class MappingValidationMixin(object):
    def __init__(self, mapping, **kwargs):
        super().__init__(**kwargs)
        self._mapping = mapping

    def validate_against_mapping(self, raw_value, error_path_str):
        if type(raw_value) not in self._mapping:
            raise AdapterValidationError('Incorrect data type for key "%s"' % error_path_str)

    def get_validator_instance(self, raw_value):
        validator_instance = self._mapping[type(raw_value)]
        if not isinstance(validator_instance, AttributeValidator):
            raise UnexpectedMappingElement('Values in mapping must be instances of AttributeValidator type')
        return validator_instance


class FreeContentCompoundedAttributeValidator(MappingValidationMixin, CompoundedAttributeValidator):
    def validate(self, parent_data, error_path=None):
        super().validate(parent_data, error_path)

        error_path, error_path_str = self._generate_error_path_pair()
        raw_value = self._get_raw_value_from_parent_data(parent_data)
        if raw_value is None:
            return
        child_attributes_names = {child.name for child in self._child_validators}
        for k, v in raw_value.items():
            if k not in child_attributes_names:
                self.validate_against_mapping(v, error_path_str + '/' + k)
                validator_instance = self.get_validator_instance(v)
                validator_instance.name = k
                validator_instance.validate(raw_value, error_path)


class FreeTypeAttributeValidator(MappingValidationMixin, AttributeValidator):
    def __init__(self, **kwargs):
        kwargs.pop('data_type', None)
        super().__init__(data_type=object, **kwargs)

    def validate(self, parent_data, error_path=None):
        super().validate(parent_data, error_path)

        error_path, error_path_str = self._generate_error_path_pair(error_path)
        raw_value = self._get_raw_value_from_parent_data(parent_data)
        if raw_value is None:
            return
        self.validate_against_mapping(raw_value, error_path_str)
        validator_instance = self.get_validator_instance(raw_value)
        validator_instance.name = self._name
        validator_instance.validate(parent_data, error_path)


class CollectionAttributeValidator(AttributeValidator):
    def __init__(self, inner_validator, **kwargs):
        kwargs.pop('data_type', None)
        super().__init__(data_type=list, **kwargs)
        self._inner_validator = inner_validator

    def validate(self, parent_data, error_path=None):
        super().validate(parent_data, error_path)

        error_path, _ = self._generate_error_path_pair(error_path)
        raw_value = self._get_raw_value_from_parent_data(parent_data)
        if raw_value is None:
            return
        self._inner_validator.name = 'collection_item'
        for v in raw_value:
            #this is hack for preserving the same validator interface as in whole application
            collection_item_parent_data = {
                'collection_item': v
            }
            self._inner_validator.validate(collection_item_parent_data, error_path)


class SchemaValidator:
    def __init__(self, child_validators):
        self._child_validators = child_validators

    def validate(self, data):
        if type(data) != dict:
            raise AdapterValidationError('Incorrect root data type')
        for child_validator in self._child_validators:
            child_validator.validate(data)
