from errors import AdapterValidationError
from base import AdapterAttribute, AdapterSearchable, AdapterMapped, BaseAdapter, AdapterCompounded, AdapterValidated, \
    AdapterAliased, AdapterInsertTarget


class AdapterObjectAttribute(AdapterAttribute, AdapterCompounded, AdapterSearchable, AdapterAliased, AdapterInsertTarget):
    def __init__(self, **kwargs):
        kwargs.pop('data_type', None)
        AdapterAttribute.__init__(self, data_type=dict, **kwargs)
        AdapterCompounded.__init__(self)
        AdapterSearchable.__init__(self, **kwargs)
        AdapterAliased.__init__(self, **kwargs)
        AdapterInsertTarget.__init__(self, **kwargs)

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
        return type(class_name, self._get_adapter_creation_base_classes(), dict(self.get_adapter_fields().items()))

    def _get_adapter_creation_base_classes(self):
        return BaseAdapter,

    def _get_adapter_instance_params(self, raw_value):
        kwargs = {
            'raw_data': raw_value,
            'editable': self._editable,
            'target_alias': self.target_alias,
            'source_aliases': self.source_aliases
        }
        return kwargs

    def search_in_attributes(self, search_name, owner_instance):
        adapter_fields = self.get_adapter_fields()
        adapter_instance = self._create_field_adapter_instance(owner_instance)
        if not adapter_instance:
            return

        searched_field = adapter_fields.get(search_name)
        if searched_field:
            return searched_field.__get__(adapter_instance, adapter_instance.__class__)

        for _, field in adapter_fields.items():
            if not (isinstance(field, AdapterSearchable) and field.searchable):
                continue
            ret = field.search_in_attributes(search_name, adapter_instance)
            if ret:
                return ret

    def search_aliased_adapter(self, target_alias, owner_instance):
        adapter_instance = self._create_field_adapter_instance(owner_instance)
        if not adapter_instance:
            return

        if self.target_alias and target_alias == self.target_alias:
            return adapter_instance

        for _, field in self.get_adapter_fields().items():
            if not isinstance(field, AdapterAliased):
                continue
            ret = field.search_aliased_adapter(target_alias, adapter_instance)
            if ret:
                return ret

    def insert_value(self, key, value, owner_instance):
        adapter_instance = self._create_field_adapter_instance(owner_instance)
        if not adapter_instance:
            raise AdapterValidationError('Value cannot be inserted to "%s" attribute because it has missing key in adapted data' % self._name)
        if adapter_instance and isinstance(adapter_instance, AdapterInsertTarget):
            adapter_instance.insert_value(key, value)

    def validate(self, owner_instance):
        AdapterAttribute.validate(self, owner_instance)
        adapter_instance = self._create_field_adapter_instance(owner_instance)
        if adapter_instance:
            AdapterCompounded.validate(self, adapter_instance)


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

    def validate(self, owner_instance=None):
        super().validate()
        for k, v in self._raw_data.items():
            if k in self.get_adapter_fields():
                continue
            attribute_instance = self._get_attribute_instance(k, v, self)
            if isinstance(attribute_instance, AdapterValidated):
                attribute_instance.validate(self)

    def insert_value(self, key, value, owner_instance=None):
        if key not in self.get_adapter_fields():
            for field_name, field in self.get_adapter_fields().items():
                if isinstance(field, AdapterInsertTarget) and field.insertable and isinstance(value, field.insert_type):
                    field.insert_value(key, value, self)
                    return

            if not self._editable:
                raise AdapterValidationError('Adapter "%s" is not editable' % self.__class__)
            attribute_instance = self._get_attribute_instance(key, value, self)
            attribute_instance.__set__(self, value)

        if not self._editable:
            raise AdapterValidationError('Adapter "%s" is not editable' % self.__class__)
        super(BaseAdapter, self).__setattr__(key, value)


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

    def search_in_attributes(self, search_name, owner_instance):
        adapter_fields = self.get_adapter_fields()
        adapter_instance = self._create_field_adapter_instance(owner_instance)
        if not adapter_instance:
            return

        searched_field = adapter_fields.get(search_name)
        if searched_field:
            return searched_field.__get__(adapter_instance, adapter_instance.__class__)

        raw_value = self._get_raw_value(owner_instance)
        search_name_raw_value = raw_value.get(search_name, None)
        if search_name_raw_value is not None:
            attribute_instance = self._get_attribute_instance(search_name, search_name_raw_value, adapter_instance)
            ret = attribute_instance.__get__(adapter_instance, self.__class__)
            if ret:
                return ret

        for _, field in adapter_fields.items():
            if not (isinstance(field, AdapterSearchable) and field.searchable):
                continue
            ret = field.search_in_attributes(search_name, adapter_instance)
            if ret:
                return ret

    def validate(self, owner_instance):
        super().validate(owner_instance)
        raw_value = self._get_raw_value(owner_instance)
        adapter_instance = self._create_field_adapter_instance(owner_instance)
        for k, v in raw_value.items():
            if k in self.get_adapter_fields():
                continue
            attribute_instance = self._get_attribute_instance(k, v, adapter_instance)
            if isinstance(attribute_instance, AdapterValidated):
                attribute_instance.validate(adapter_instance)


class AdapterFreeTypeAttribute(AdapterAttribute, AdapterMapped, AdapterSearchable, AdapterAliased):
    def __init__(self, mapping, **kwargs):
        kwargs.pop('data_type', None)
        AdapterAttribute.__init__(self, data_type=object, **kwargs)
        AdapterMapped.__init__(self, mapping, **kwargs)
        AdapterSearchable.__init__(self, **kwargs)
        AdapterAliased.__init__(self, **kwargs)

    def __get__(self, owner_instance, owner):
        raw_value = self._get_raw_value(owner_instance)
        if raw_value is None:
            return

        attribute_instance = self._get_attribute_instance(self._name, raw_value, owner_instance)
        return attribute_instance.__get__(owner_instance, owner)

    def search_in_attributes(self, search_name, owner_instance):
        raw_value = self._get_raw_value(owner_instance)
        if raw_value is None:
            return

        attribute_instance = self._get_attribute_instance(self._name, raw_value, owner_instance)
        if isinstance(attribute_instance, AdapterSearchable):
            return attribute_instance.search_in_attributes(search_name, owner_instance)

    def search_aliased_adapter(self, alias, owner_instance):
        raw_value = self._get_raw_value(owner_instance)
        if raw_value is None:
            return

        attribute_instance = self._get_attribute_instance(self._name, raw_value, owner_instance)
        if isinstance(attribute_instance, AdapterAliased):
            return attribute_instance.search_aliased_adapter(alias, owner_instance)

    def insert_value(self, key, value, owner_instance):
        raw_value = self._get_raw_value(owner_instance)
        if raw_value is None:
            return

        attribute_instance = self._get_attribute_instance(self._name, raw_value, owner_instance)
        if isinstance(attribute_instance, AdapterInsertTarget):
            attribute_instance.insert_value(key, value, owner_instance)

    def validate(self, owner_instance):
        AdapterAttribute.validate(self, owner_instance)
        raw_value = self._get_raw_value(owner_instance)
        if not raw_value:
            return

        attribute_instance = self._get_attribute_instance(self._name, raw_value, owner_instance)
        if isinstance(attribute_instance, AdapterValidated):
            attribute_instance.validate(owner_instance)

    def _validate_set_data(self, value):
        if not self._editable:
            raise AdapterValidationError('Attribute "%s" is not editable' % self._name)
        self._validate_against_mapping(value)