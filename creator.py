import inspect


class AdapterValidationError(Exception):
    pass


class AdapterAttribute:
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
        if self._required and raw_value is None:
            raise AdapterValidationError('Missing key "%s"' % self._name)
        if raw_value is not None and not isinstance(raw_value, self._data_type):
            raise AdapterValidationError('Incorrect data type for key "%s"' % self._name)
        if raw_value is not None and not raw_value and self._required:
            raise AdapterValidationError('Empty value for key "%s' % self._name)
        return raw_value

    def _get_owner_instance_raw_data(self, owner_instance):
        return owner_instance.serialize_to_raw_data()

    def __set__(self, owner_instance, value):
        self._validate_set_data(value)
        self._get_owner_instance_raw_data(owner_instance)[self._name] = value

    def _validate_set_data(self, value):
        if not self._editable:
            raise AdapterValidationError('Attribute "%s" is not editable' % self._name)
        if self._data_type != type(value):
            raise AdapterValidationError('Attribute requires "%s" data type' % str(self._data_type))

    def validate(self, owner_instance):
        if self._get_raw_value(owner_instance) is not None:
            return

        required_with = set(self._required_with)
        for k, _ in self._get_owner_instance_raw_data(owner_instance).items():
            if k in required_with:
                required_with.remove(k)
        if required_with:
            s = "Attribute %s required together with %s" % (self._name, ", ".join([k for k in self._required_with]))
            raise AdapterValidationError(s)


class AdapterCompounded:
    def __init__(self, searchable=False, **kwargs):
        self.searchable = searchable

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
        owner_instance = self
        for _, field in self.get_adapter_fields():
            field.validate(owner_instance)


class BaseAdapter(AdapterCompounded):
    def __init__(self, raw_data, **kwargs):
        self._raw_data = raw_data
        super().__init__(**kwargs)

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
            return getattr(adapter_field_instance, search_name, None)

    def serialize_to_raw_data(self):
        return self._raw_data


class AdapterObjectAttribute(AdapterAttribute, AdapterCompounded):
    def __init__(self, **kwargs):
        kwargs.pop('data_type', None)
        AdapterAttribute.__init__(self, data_type=dict, **kwargs)
        AdapterCompounded.__init__(self, **kwargs)

    def __get__(self, owner_instance, owner):
        return self.create_field_adapter_instance(owner_instance)

    def create_field_adapter_instance(self, owner_instance):
        adapter_class = self._create_adapter_class(self._name)
        return adapter_class(**self._get_adapter_instance_params(owner_instance))

    def _create_adapter_class(self, name):
        class_name = '%sAdapterType' % name.lower().title()
        return type(class_name, self._get_adapter_creation_base_classes(), dict(self.get_adapter_fields()))

    def _get_adapter_creation_base_classes(self):
        return (BaseAdapter,)

    def _get_adapter_instance_params(self, owner_instance):
        kwargs = {'raw_data': self._get_raw_value(owner_instance)}
        return kwargs

    def validate(self, owner_instance=None):
        if not owner_instance:
            raise ValueError('Owner instance parameter not filled.')
        AdapterAttribute.validate(self, owner_instance)
        raw_value = self._get_raw_value(owner_instance)
        if raw_value is None:
            return
        adapter_instance = self.create_field_adapter_instance(owner_instance)
        adapter_instance.validate()


class AdapterMapped:
    def __init__(self, mapping, **kwargs):
        self._mapping = mapping

    def _get_attribute_adapter_instance(self, name, raw_value, owner_instance=None):
        owner_instance = self
        self._validate_against_mapping(name, raw_value)
        adapter_attribute_instance = self._mapping[type(raw_value)]
        adapter_attribute_instance.__set_name__(owner_instance.__class__, name)
        return adapter_attribute_instance

    def _validate_against_mapping(self, name, raw_value):
        if type(raw_value) not in self._mapping:
            raise AdapterValidationError('Incorrect data type for key "%s"' % name)


class AdapterFreeContent(BaseAdapter, AdapterMapped):
    def __init__(self, **kwargs):
        BaseAdapter.__init__(self, **kwargs)
        AdapterMapped.__init__(self, **kwargs)

    def __getattr__(self, item):
        for k, v in self._raw_data.items():
            if k != item:
                continue
            adapter_attribute = self._get_attribute_adapter_instance(k, v)
            ret = adapter_attribute.__get__(self, self.__class__)
            return ret
        return super().__getattr__(item)

    def validate(self, owner_instance=None):
        super().validate()
        owner_instance = self
        user_defined_fields = {f[0] for f in self.get_adapter_fields()}
        for k, v in self._raw_data.items():
            if k in user_defined_fields:
                continue
            self._get_attribute_adapter_instance(k, v).validate(owner_instance)


class AdapterObjectFreeContentAttribute(AdapterObjectAttribute, AdapterCompounded, AdapterMapped):
    def __init__(self, **kwargs):
        AdapterObjectAttribute.__init__(self, **kwargs)
        AdapterCompounded.__init__(self, **kwargs)
        AdapterMapped.__init__(self, **kwargs)

    def _get_adapter_creation_base_classes(self):
        return (AdapterFreeContent,)

    def _get_adapter_instance_params(self, owner_instance):
        kwargs = super()._get_adapter_instance_params(owner_instance)
        kwargs.update({'mapping': self._mapping})
        return kwargs


class AdapterFreeTypeAttribute(AdapterAttribute, AdapterMapped):
    def __init__(self, **kwargs):
        kwargs.pop('data_type', None)
        AdapterAttribute.__init__(self, data_type=object, **kwargs)
        AdapterMapped.__init__(self, **kwargs)

    def __get__(self, owner_instance, owner):
        raw_value = self._get_raw_value(owner_instance)
        adapter_attribute_instance = self._get_attribute_adapter_instance(self._name, raw_value, owner_instance)
        return adapter_attribute_instance.__get__(owner_instance, owner)

    def _get_attribute_adapter_instance(self, name, raw_value, owner_instance=None):
        if not owner_instance:
            raise ValueError('Owner instance parameter not filled.')
        return super()._get_attribute_adapter_instance(name, raw_value, owner_instance)

    def validate(self, owner_instance):
        super().validate(owner_instance)
        adapter_instance = self.__get__(owner_instance, owner_instance.__class__)
        adapter_instance.validate()


class RelationshipItem(AdapterObjectAttribute):
    type = AdapterAttribute(data_type=str)
    id = AdapterAttribute(data_type=str)

attributes_mapping = {
    str: (AdapterAttribute(data_type=str))
}

relationship_mapping = {
    dict: (RelationshipItem(data_type=dict))
}

hello_mapping = {
    str: AdapterAttribute(data_type=str),
    dict: AdapterObjectAttribute(data_type=dict, required=False)
}


class AttributesObject(AdapterObjectFreeContentAttribute):
    hello = AdapterFreeTypeAttribute(mapping=hello_mapping)


class JSONApi(BaseAdapter):
    type = AdapterAttribute(data_type=str)
    id = AdapterAttribute(data_type=str)
    attributes = AttributesObject(mapping=attributes_mapping, searchable=True, required=False)
    relationships = AdapterObjectFreeContentAttribute(mapping=relationship_mapping, searchable=True)


data = {
    "id": "1",
    "type": "Siema",
    "attributes": {
        'hello': {}
    },
    "relationships": {
        "author": {
            "type": "s",
            "id": "544"
        },
    }
}

j = JSONApi(data, searchable=True)
j.validate()

#TODO searchable on which class
# TODO search on free content's free content attrs ??