import inspect


class AdapterValidationError(Exception):
    pass


class AdapterDataError(Exception):
    pass


class AdapterAttribute:
    def __init__(self, data_type, required=True, required_with=None, editable=True, **kwargs):
        self._data_type = data_type
        self._required = required
        self._required_with = required_with if required_with else []
        self._editable = editable

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner):
        return self._get_from_raw_data(instance)

    def _get_from_raw_data(self, instance):
        raw_value = None
        for k, v in self._get_instance_raw_data(instance).items():
            if k != self._name:
                continue
            raw_value = v
        if not raw_value:
            raise AdapterDataError('Missing key %s' % self._name)
        if not isinstance(raw_value, self._data_type):
            raise AdapterDataError('Incorrect data type for key %s' % self._name)
        return raw_value

    def _get_instance_raw_data(self, instance):
        return instance.serialize_to_raw_data()

    def __set__(self, instance, value):
        self._validate_set_data(value)
        self._get_instance_raw_data(instance)[self._name] = value

    def _validate_set_data(self, value):
        if not self._editable:
            raise AdapterValidationError('Attribute %s is not editable' % self._name)
        if self._data_type != type(value):
            raise AdapterValidationError('Attribute requires %s data type' % str(self._data_type))

    def validate(self, instance):
        required_with = set(self._required_with)
        required_satisfied = False
        for k, _ in self._get_instance_raw_data(instance).items():
            if k in required_with:
                required_with.remove(k)
            if k == self._name:
                required_satisfied = True

        if not required_satisfied and self._required:
            raise AdapterValidationError("Attribute %s is required" % self._name)
        if required_with and self._required:
            s = "Attribute %s required together with %s" % (self._name, ", ".join([k for k in self._required_with]))
            raise AdapterValidationError(s)


class AdapterCompounded:
    def __init__(self, searchable=False, **kwargs):
        self.searchable = searchable
        super().__init__()

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
            owner_instance = self
        for _, field in self.get_adapter_fields():
            field.validate(owner_instance)


class BaseAdapter(AdapterCompounded):
    def __init__(self, raw_data, *args, **kwargs):
        self._raw_data = raw_data
        super().__init__(*args, **kwargs)

    def __getattr__(self, item):
        value = self.search_in_attributes_and_return_proper_type(item)
        if not value:
            raise AttributeError(item)
        return value

    def search_in_attributes_and_return_proper_type(self, search_name):
        if not self.searchable:
            return

        for _, field in self.get_adapter_fields():
            if not isinstance(field, AdapterObjectAttribute) or not field.searchable:
                continue
            adapter_field_instance = field.create_field_adapter_instance(self)
            value = getattr(adapter_field_instance, search_name, None)
            if value:
                return value

    def serialize_to_raw_data(self):
        return self._raw_data


class AdapterObjectAttribute(AdapterAttribute, AdapterCompounded):
    def __init__(self, **kwargs):
        kwargs.pop('data_type', None)
        AdapterAttribute.__init__(self, data_type=dict, **kwargs)
        AdapterCompounded.__init__(self, **kwargs)

    def __get__(self, instance, owner):
        return self.create_field_adapter_instance(instance)

    def create_field_adapter_instance(self, instance):
        adapter_class = self._create_adapter_class(self._name)
        return adapter_class(**self._get_adapter_instance_params(instance))

    def _create_adapter_class(self, name):
        class_name = '%sAdapterType' % name.lower().title()
        return type(class_name, self._get_adapter_creation_base_classes(), dict(self.get_adapter_fields()))

    def _get_adapter_creation_base_classes(self):
        return (BaseAdapter,)

    def _get_adapter_instance_params(self, instance):
        kwargs = {'raw_data': self._get_from_raw_data(instance)}
        return kwargs

    def validate(self, instance=None):
        if not instance:
            raise ValueError('Instance parameter not filled.')
        AdapterAttribute.validate(self, instance)
        AdapterCompounded.validate(self, instance)


class BaseFreeContentAdapter:


class AdapterFreeContent(BaseAdapter):
    def __init__(self, mapping, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = mapping

    def __getattr__(self, item):
        for k, v in self._raw_data.items():
            if k != item:
                continue
            if type(v) not in self.mapping:
                raise AdapterDataError("Attribute's type not allowed")
            adapter_attribute = self._create_attribute_adapter_instance(k, v)
            ret = adapter_attribute.__get__(self, self.__class__)
            return ret
        return super().__getattr__(item)

    def _create_attribute_adapter_instance(self, name, value):
        adapter_attribute_class = self.mapping[type(value)][0]
        adapter_instance_kwargs = self.mapping[type(value)][1]
        adapter_instance_kwargs.update({'data_type': type(value)})
        adapter_attribute = adapter_attribute_class(**adapter_instance_kwargs)
        adapter_attribute.__set_name__(self.__class__, name)
        return adapter_attribute


class AdapterObjectFreeContentAttribute(AdapterObjectAttribute, AdapterCompounded):
    def __init__(self, mapping, **kwargs):
        self._mapping = mapping
        super().__init__(**kwargs)

    def _get_adapter_creation_base_classes(self):
        return (AdapterFreeContent,)

    def _get_adapter_instance_params(self, instance):
        kwargs = super()._get_adapter_instance_params(instance)
        kwargs.update({'mapping': self._mapping})
        return kwargs


class RelationshipItem(AdapterObjectAttribute):
    type = AdapterAttribute(data_type=str)
    id = AdapterAttribute(data_type=str)

attributes_mapping = {
    str: (AdapterAttribute(data_type=str))
}

relationship_mapping = {
    dict: (RelationshipItem(data_type=dict))
}


class JSONApi(BaseAdapter):
    type = AdapterAttribute(data_type=str, required=False)
    id = AdapterAttribute(data_type=str)
    attributes = AdapterObjectFreeContentAttribute(attributes_mapping, searchable=True)
    relationships = AdapterObjectFreeContentAttribute(relationship_mapping, searchable=True)


data = {
    "type": "articles",
    "id": "1",
    "attributes": {
        "title": "Rails is Omakase",
        "name": "Siemaeniu"
    },
    "relationships": {
        "author": {
            "type": 2,
            "id": "544"
        },
        'a': 2
    }
}

j = JSONApi(data, searchable=True)
