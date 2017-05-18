import collections

import validators


class SchemaAttribute:
    def __init__(self, data_type, required=True, required_with=None):
        self._data_type = data_type
        self._required = required
        self._required_with = required_with if required_with else []
        self._name = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def get_validator(self):
        return validators.AttributeValidator(
            name=self._name,
            data_type=self._data_type,
            required=self._required,
            required_with=self._required_with
        )


class SchemasMetaClass(type):
    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(mcls, name, bases, attrs):
        ordered_attributes = collections.OrderedDict()
        for attr, obj in attrs.items():
            if isinstance(obj, SchemaAttribute):
                ordered_attributes[attr] = obj
        attrs['__ordered_attributes__'] = ordered_attributes

        cls = super(SchemasMetaClass, mcls).__new__(mcls, name, bases, attrs)
        for attr, obj in attrs.items():
            if isinstance(obj, SchemaAttribute):
                obj.name = attr
        return cls


class SchemaCompoundedMixin(object, metaclass=SchemasMetaClass):
    def get_schema_attributes(self):
        return self.__class__.__ordered_attributes__

    def get_attributes_validators(self):
        validators = []
        for attr_name, attribute in self.get_schema_attributes().items():
            validators.append(attribute.get_validator())
        return validators


class SchemaCompoundedAttribute(SchemaCompoundedMixin, SchemaAttribute):
    def __init__(self, **kwargs):
        kwargs.pop('data_type', None)
        super().__init__(data_type=dict, **kwargs)

    def get_validator(self):
        return validators.CompoundedAttributeValidator(
            child_validators=self.get_attributes_validators(),
            name=self._name,
            required=self._required,
            required_with=self._required_with
        )


class MappingMixin(object):
    def __init__(self, mapping, **kwargs):
        super().__init__(**kwargs)
        self._mapping = mapping


class SchemaFreeContentCompoundedAttribute(MappingMixin, SchemaCompoundedAttribute):
    def get_validator(self):
        validator_mapping = {}
        for k, v in self._mapping.items():
            validator_mapping[k] = v.get_validator()

        return validators.FreeContentCompoundedAttributeValidator(
            mapping=validator_mapping,
            child_validators=self.get_attributes_validators(),
            name=self._name,
            required=self._required,
            required_with=self._required_with
        )


class SchemaFreeTypeAttribute(MappingMixin, SchemaAttribute):
    def __init__(self, **kwargs):
        kwargs.pop('data_type', None)
        super().__init__(data_type=object, **kwargs)

    def get_validator(self):
        validator_mapping = {}
        for k, v in self._mapping.items():
            validator_mapping[k] = v.get_validator()

        return validators.FreeTypeAttributeValidator(
            mapping=validator_mapping,
            name=self._name,
            required=self._required,
            required_with=self._required_with
        )


class SchemaCollectionAttribute(SchemaAttribute):
    def __init__(self, inner_attribute, **kwargs):
        kwargs.pop('data_type', None)
        super().__init__(data_type=list, **kwargs)
        self._inner_attribute = inner_attribute

    def get_validator(self):
        return validators.CollectionAttributeValidator(
            inner_validator=self._inner_attribute.get_validator(),
            name=self._name,
            required=self._required,
            required_with=self._required_with
        )


class Schema(SchemaCompoundedMixin):
    def get_validator(self):
        return validators.SchemaValidator(self.get_attributes_validators())