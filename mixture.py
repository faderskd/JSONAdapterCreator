from errors import AdapterValidationError
from base import AdapterAttribute, AdapterSearchable, AdapterMapped, BaseAdapter, AdapterInsertTarget, AdapterValidated


class AdapterObjectAttribute(AdapterAttribute, AdapterInsertTarget, AdapterSearchable):
    def __init__(self, **kwargs):
        kwargs.pop('data_type', None)
        AdapterAttribute.__init__(self, data_type=dict, **kwargs)
        AdapterInsertTarget.__init__(self, **kwargs)
        AdapterSearchable.__init__(self, **kwargs)

    def __get__(self, owner_instance, owner):
        return self._create_field_adapter_instance(owner_instance)

    def _create_field_adapter_instance(self, owner_instance):
        raw_value = self._get_raw_value(owner_instance)
        if raw_value is None:
            return
        adapter_class = self._create_adapter_class(self._name)
        return adapter_class(**self._get_adapter_instance_params(raw_value))

    def _create_adapter_class(self, name):
        class_name = '%sAdapterType' % name.lower().title()
        return type(class_name, self._get_adapter_creation_base_classes(), dict(self.get_adapter_fields()))

    def _get_adapter_creation_base_classes(self):
        return BaseAdapter,

    def _get_adapter_instance_params(self, raw_value):
        kwargs = {
            'raw_data': raw_value,
            'editable': self._editable
        }
        return kwargs

    def search_in_attributes_and_return_proper_type(self, search_name, owner_instance):
        if not self.searchable:
            return
        adapter_instance = self._create_field_adapter_instance(owner_instance)
        return getattr(adapter_instance, search_name, None)

    def validate(self, owner_instance):
        AdapterAttribute.validate(self, owner_instance)
        adapter_instance = self._create_field_adapter_instance(owner_instance)
        if adapter_instance and isinstance(adapter_instance, AdapterValidated):
            adapter_instance.validate()

    def insert_value(self, key, value, owner_instance):
        if not self._editable:
            raise AdapterValidationError('This adapter object is not editable')

        adapter_instance = self._create_field_adapter_instance(owner_instance)
        setattr(adapter_instance, key, value)


class AdapterFreeContent(BaseAdapter, AdapterMapped):
    def __init__(self, raw_data, mapping, **kwargs):
        BaseAdapter.__init__(self, raw_data, **kwargs)
        AdapterMapped.__init__(self, mapping, **kwargs)

    def __getattr__(self, item):
        raw_value = self._raw_data.get(item, None)
        if raw_value is not None:
            attribute_instance = self._get_attribute_instance(item, raw_value, self)
            ret = attribute_instance.__get__(self, self.__class__)
            return ret
        return super().__getattr__(item)

    def insert_value(self, key, value, owner_instance=None):
        adapter_fields_names = {f[0] for f in self.get_adapter_fields()}
        if key not in adapter_fields_names:
            for field_name, field in self._get_insertable_fields():
                if field.insertable and isinstance(value, field.insert_type):
                    field.insert_value(key, value, self)
                    return
            adapter_instance = self._get_attribute_instance(key, value, self)
            adapter_instance.__set__(self, value)
        super(BaseAdapter, self).__setattr__(key, value)

    def validate(self, owner_instance=None):
        super().validate()
        user_defined_fields = {f[0] for f in self.get_adapter_fields()}
        for k, v in self._raw_data.items():
            if k in user_defined_fields:
                continue
            attribute_instance = self._get_attribute_instance(k, v, self)
            if isinstance(attribute_instance, AdapterValidated):
                attribute_instance.validate(self)


class AdapterObjectFreeContentAttribute(AdapterObjectAttribute, AdapterMapped):
    def __init__(self, mapping, **kwargs):
        AdapterObjectAttribute.__init__(self, **kwargs)
        AdapterMapped.__init__(self, mapping, **kwargs)

    def _get_adapter_creation_base_classes(self):
        return AdapterFreeContent,

    def _get_adapter_instance_params(self, raw_value):
        kwargs = super()._get_adapter_instance_params(raw_value)
        kwargs.update({'mapping': self._mapping})
        return kwargs

    def _validate_set_data(self, value):
        if not self._editable:
            raise AdapterValidationError('Attribute "%s" is not editable' % self._name)
        self._validate_against_mapping(value)


class AdapterFreeTypeAttribute(AdapterAttribute, AdapterMapped, AdapterSearchable, AdapterInsertTarget):
    def __init__(self, mapping, **kwargs):
        kwargs.pop('data_type', None)
        AdapterAttribute.__init__(self, data_type=object, **kwargs)
        AdapterMapped.__init__(self, mapping, **kwargs)
        AdapterSearchable.__init__(self, **kwargs)
        AdapterInsertTarget.__init__(self, **kwargs)

    def search_in_attributes_and_return_proper_type(self, search_name, owner_instance):
        if not self.searchable:
            return
        value = self.__get__(owner_instance, owner_instance.__class__)
        if isinstance(value, BaseAdapter):
            return getattr(value, search_name, None)

    def __get__(self, owner_instance, owner):
        raw_value = self._get_raw_value(owner_instance)
        if raw_value is None:
            return
        attribute_instance = self._get_attribute_instance(self._name, raw_value, owner_instance)
        return attribute_instance.__get__(owner_instance, owner)

    def validate(self, owner_instance):
        AdapterAttribute.validate(self, owner_instance)
        adapter_instance = self.__get__(owner_instance, owner_instance.__class__)
        if isinstance(adapter_instance, BaseAdapter):
            adapter_instance.validate()

    def _validate_set_data(self, value):
        if not self._editable:
            raise AdapterValidationError('Attribute "%s" is not editable' % self._name)
        self._validate_against_mapping(value)

    def insert_value(self, key, value, owner_instance):
        adapter_instance = self.__get__(owner_instance, owner_instance.__class__)
        if isinstance(adapter_instance, AdapterInsertTarget):
            adapter_instance.insert_value(key, value, owner_instance)
        else:
            raise AdapterValidationError('Inserted value not match to any adapter field')