import inspect
from abc import ABCMeta, abstractmethod

from errors import AdapterValidationError


class Validated(metaclass=ABCMeta):
    @abstractmethod
    def validate(self, owner_instance=None):
        pass


class AdapterAttribute(Validated):
    def __init__(self, data_type, required=True, required_with=None, editable=True, **kwargs):
        self._data_type = data_type
        self._required = required
        self._required_with = required_with if required_with else []
        self._editable = editable

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, owner_instance, owner):
        return self._get_raw_value(owner_instance)

    def _get_raw_value(self, owner_instance):
        raw_value = self._get_owner_instance_raw_data(owner_instance).get(self._name, None)
        self._validate_raw_value(raw_value)
        return raw_value

    def _get_owner_instance_raw_data(self, owner_instance):
        return owner_instance.serialize_to_raw_data()

    def _validate_raw_value(self, raw_value):
        if self._required and raw_value is None:
            raise AdapterValidationError('Missing key "%s"' % self._name)
        if raw_value is not None and not isinstance(raw_value, self._data_type):
            raise AdapterValidationError('Incorrect data type for key "%s"' % self._name)

    def __set__(self, owner_instance, value):
        self._validate_set_data(value)
        self._get_owner_instance_raw_data(owner_instance)[self._name] = value

    def _validate_set_data(self, value):
        if not self._editable:
            raise AdapterValidationError('Attribute "%s" is not editable' % self._name)
        if self._data_type != type(value):
            raise AdapterValidationError('Attribute requires "%s" data type' % str(self._data_type))

    def validate(self, owner_instance=None):
        if not owner_instance:
            raise ValueError('Owner instance parameter unfilled')

        raw_value = self._get_owner_instance_raw_data(owner_instance).get(self._name, None)
        self._validate_raw_value(raw_value)
        if raw_value is None:
            return

        required_with = set(self._required_with)
        for k, _ in self._get_owner_instance_raw_data(owner_instance).items():
            if k in required_with:
                required_with.remove(k)
        if required_with:
            s = "Attribute %s required together with %s" % (self._name, ", ".join([k for k in self._required_with]))
            raise AdapterValidationError(s)


class AdapterCompounded(Validated):
    def get_adapter_fields(self):
        fields = []
        for field_name, field in self._get_user_defined_fields():
            if isinstance(field, AdapterAttribute):
                fields.append((field_name, field))
        return fields

    def _get_user_defined_fields(self):
        attributes = inspect.getmembers(self.__class__, lambda a: not (inspect.isroutine(a)))
        fields = [a for a in attributes if not (a[0].startswith('__') and a[0].endswith('__'))]
        return fields

    def validate(self, owner_instance=None):
        if not owner_instance:
            raise ValueError('Owner instance parameter unfilled')
        for _, field in self.get_adapter_fields():
            if isinstance(field, Validated):
                field.validate(owner_instance)


class AdapterSearchable(metaclass=ABCMeta):
    def __init__(self, searchable=False, **kwargs):
        self.searchable = searchable

    @abstractmethod
    def search_in_attributes_and_return_proper_type(self, search_name, owner_instance=None):
        pass


class AdapterMapped:
    def __init__(self, mapping, **kwargs):
        self._mapping = mapping

    def _get_adapter_attribute_instance(self, name, raw_value, owner_instance=None):
        if not owner_instance:
            raise ValueError('Owner instance parameter unfilled')

        self._validate_against_mapping(name, raw_value)
        adapter_attribute_instance = self._mapping[type(raw_value)]
        adapter_attribute_instance.__set_name__(owner_instance.__class__, name)
        return adapter_attribute_instance

    def _validate_against_mapping(self, name, raw_value):
        if type(raw_value) not in self._mapping:
            raise AdapterValidationError('Incorrect data type for key "%s"' % name)


class BaseAdapter(AdapterCompounded, AdapterSearchable):
    def __init__(self, raw_data, **kwargs):
        self._raw_data = raw_data
        AdapterCompounded.__init__(self)
        AdapterSearchable.__init__(self, **kwargs)

    def __getattr__(self, item):
        value = self.search_in_attributes_and_return_proper_type(item)
        if not value:
            raise AttributeError(item)
        return value

    def search_in_attributes_and_return_proper_type(self, search_name, owner_instance=None):
        if not self.searchable:
            return

        for _, field in self.get_adapter_fields():
            if not isinstance(field, AdapterSearchable):
                continue
            ret = field.search_in_attributes_and_return_proper_type(search_name, self)
            if ret:
                return ret

    def serialize_to_raw_data(self):
        return self._raw_data

    def validate(self, owner_instance=None):
        super().validate(self)