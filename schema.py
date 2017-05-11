import collections

import validators


class SchemaAttribute:
    def __init__(self, data_type, required=True, required_with=None):
        self._data_type = data_type
        self._required = required
        self._required_with = required_with if required_with else []

    def __set_name__(self, schema, name):
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
                obj.__set_name__(cls, attr)
        return cls


class SchemaCompoundedMixin(object, metaclass=SchemasMetaClass):
    def get_schema_attributes(self):
        return self.__class__.__ordered_attributes__


class Schema(SchemaCompoundedMixin):
    def get_validator(self):
        return validators.SchemaValidator(self._get_child_validators())

    def _get_child_validators(self):
        child_validators = []
        for attr_name, attribute in self.get_schema_attributes().items():
            child_validators.append(attribute.get_validator())
        return child_validators