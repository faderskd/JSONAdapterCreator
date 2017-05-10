import collections
from abc import abstractmethod

from errors import AdapterValidationError


class AdapterValidated:
    @abstractmethod
    def validate(self, owner_instance):
        pass


class AdapterSearchable:
    def __init__(self, searchable=False, **kwargs):
        self.__dict__['searchable'] = searchable

    @abstractmethod
    def search_in_attributes(self, search_name, owner_instance):
        pass


class AdapterAliased:
    def __init__(self, source_aliases=None, target_alias=None, **kwargs):
        self.__dict__['source_aliases'] = source_aliases if source_aliases else []
        self.__dict__['target_alias'] = target_alias

    @abstractmethod
    def search_aliased_adapter(self, target_alias, owner_instance):
        pass


class AdapterInsertTarget:
    def __init__(self, insertable=False, insert_type=object, **kwargs):
        self.__dict__['insertable'] = insertable
        self.__dict__['insert_type'] = insert_type

    @abstractmethod
    def insert_value(self, key, value, owner_instance):
        pass


class AdapterAttribute(AdapterValidated, AdapterAliased):
    def __init__(self, data_type, required=True, required_with=None, editable=True, **kwargs):
        AdapterValidated.__init__(self)
        AdapterAliased.__init__(self, **kwargs)
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
            raise AdapterValidationError('Missing key "%s" in adapted data' % self._name)
        if raw_value is not None and not isinstance(raw_value, self._data_type):
            raise AdapterValidationError('Incorrect data type for key "%s" in adapted data' % self._name)

    def __set__(self, owner_instance, value):
        self._validate_set_data(value)
        self._get_owner_instance_raw_data(owner_instance)[self._name] = value

    def _validate_set_data(self, value):
        if not self._editable:
            raise AdapterValidationError('Attribute "%s" is not editable' % self._name)
        if self._data_type != type(value):
            raise AdapterValidationError('Attribute requires "%s" data type' % str(self._data_type))

    def validate(self, owner_instance):
        raw_value = self._get_owner_instance_raw_data(owner_instance).get(self._name, None)
        self._validate_raw_value(raw_value)
        if raw_value is None:
            return

        required_with = set(self._required_with)
        for k, _ in self._get_owner_instance_raw_data(owner_instance).items():
            if k in required_with:
                required_with.remove(k)
        if required_with:
            s = 'Attribute "%s" required together with "%s"' % (self._name, ", ".join([k for k in self._required_with]))
            raise AdapterValidationError(s)

    def search_aliased_adapter(self, target_alias, owner_instance):
        if self.target_alias and self.target_alias == target_alias:
            return self._get_raw_value(owner_instance)


class AdapterBaseMetaClass(type):
    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(mcls, name, bases, attrs):
        ordered_fields = collections.OrderedDict()
        for attr, obj in attrs.items():
            if isinstance(obj, AdapterAttribute):
                ordered_fields[attr] = obj
        attrs['__ordered_fields__'] = ordered_fields

        cls = super(AdapterBaseMetaClass, mcls).__new__(mcls, name, bases, attrs)
        for attr, obj in attrs.items():
            if isinstance(obj, AdapterAttribute):
                ordered_fields[attr] = obj
                obj.__set_name__(cls, attr)
        return cls


class AdapterCompounded(AdapterValidated, metaclass=AdapterBaseMetaClass):
    def get_adapter_fields(self):
        return self.__class__.__ordered_fields__

    def validate(self, owner_instance):
        for _, field in self.get_adapter_fields().items():
            if isinstance(field, AdapterValidated):
                field.validate(owner_instance)


class AdapterMapped:
    def __init__(self, mapping, **kwargs):
        self.__dict__['_mapping'] = mapping

    def _get_attribute_instance(self, attribute_name, raw_value, owner_instance):
        self._validate_against_mapping(raw_value)
        attribute_instance = self._mapping[type(raw_value)]
        if not isinstance(attribute_instance, AdapterAttribute):
            raise AdapterValidationError('Values in mapping must be instances of AdapterAttribute type')

        attribute_instance.__set_name__(owner_instance.__class__, attribute_name)
        return attribute_instance

    def _validate_against_mapping(self, raw_value):
        if type(raw_value) not in self._mapping:
            raise AdapterValidationError('Data type not in types mapping')


class BaseAdapter(AdapterSearchable, AdapterCompounded, AdapterAliased, AdapterInsertTarget):
    def __init__(self, raw_data, editable=True, **kwargs):
        self.__dict__['_raw_data'] = raw_data
        self.__dict__['_editable'] = editable
        kwargs.pop('searchable', None)
        AdapterCompounded.__init__(self)
        AdapterSearchable.__init__(self, serchable=True, **kwargs)
        AdapterAliased.__init__(self, **kwargs)
        AdapterInsertTarget.__init__(self, **kwargs)

    def __getattr__(self, item):
        value = None
        if item in self.source_aliases:
            value = self.search_aliased_adapter(item)
        if not value:
            value = self.search_in_attributes(item)
        if not value:
            raise AttributeError(item)
        return value

    def search_aliased_adapter(self, target_alias, owner_instance=None):
        if self.target_alias and target_alias == self.taget_alias:
            return self

        for _, field in self.get_adapter_fields().items():
            if not isinstance(field, AdapterAliased):
                continue
            ret = field.search_aliased_adapter(target_alias, self)
            if ret:
                return ret

    def search_in_attributes(self, search_name, owner_instance=None):
        for _, field in self.get_adapter_fields().items():
            if not (isinstance(field, AdapterSearchable) and field.searchable):
                continue
            ret = field.search_in_attributes(search_name, self)
            if ret:
                return ret

    def __setattr__(self, key, value):
        self.insert_value(key, value)

    def insert_value(self, key, value, owner_instance=None):
        if key not in self.get_adapter_fields():
            for field_name, field in self.get_adapter_fields().items():
                if isinstance(field, AdapterInsertTarget) and field.insertable and isinstance(value, field.insert_type):
                    field.insert_value(key, value, self)
                    return
            raise AdapterValidationError('Inserted value not match to any adapter field')

        if not self._editable:
            raise AdapterValidationError('Adapter "%s" is not editable' % self.__class__)
        super().__setattr__(key, value)

    def serialize_to_raw_data(self):
        return self._raw_data

    def validate(self, owner_instance=None):
        super().validate(self)