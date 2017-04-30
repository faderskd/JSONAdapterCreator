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
        return self._get_raw_value(instance)

    def _get_raw_value(self, instance):
        raw_value = self._get_instance_raw_data(instance).get(self._name, None)
        if self._required and not raw_value:
            raise AdapterDataError('Missing key "%s"' % self._name)
        if raw_value and not isinstance(raw_value, self._data_type):
            raise AdapterDataError('Incorrect data type for key "%s"' % self._name)
        return raw_value

    def _get_instance_raw_data(self, instance):
        return instance.serialize_to_raw_data()

    def __set__(self, instance, value):
        self._validate_set_data(value)
        self._get_instance_raw_data(instance)[self._name] = value

    def _validate_set_data(self, value):
        if not self._editable:
            raise AdapterValidationError('Attribute "%s" is not editable' % self._name)
        if self._data_type != type(value):
            raise AdapterValidationError('Attribute requires "%s" data type' % str(self._data_type))

    def validate(self, owner_instance):
        if not self._get_raw_value(owner_instance):
            return

        required_with = set(self._required_with)
        for k, _ in self._get_instance_raw_data(owner_instance).items():
            if k in required_with:
                required_with.remove(k)
        if required_with:
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
            return getattr(adapter_field_instance, search_name, None)

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
        kwargs = {'raw_data': self._get_raw_value(instance)}
        return kwargs

    def validate(self, owner_instance=None):
        if not owner_instance:
            raise ValueError('Instance parameter not filled.')
        AdapterAttribute.validate(self, owner_instance)
        raw_value = self._get_raw_value(owner_instance)
        if not raw_value:
            return
        adapter_instance = self.create_field_adapter_instance(owner_instance)
        adapter_instance.validate()


class BaseFreeContent:
    def __init__(self, mapping):
        self._mapping = mapping


class AdapterFreeContent(BaseAdapter):
    def __init__(self, mapping, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mapping = mapping

    def __getattr__(self, item):
        for k, v in self._raw_data.items():
            if k != item:
                continue
            if type(v) not in self._mapping:
                raise AdapterDataError("Key's '%s' type not allowed" % k)
            adapter_attribute = self._get_attribute_adapter_instance(k, v)
            ret = adapter_attribute.__get__(self, self.__class__)
            return ret
        return super().__getattr__(item)

    def _get_attribute_adapter_instance(self, name, raw_value):
        adapter_attribute_instance = self._mapping[type(raw_value)]
        adapter_attribute_instance.__set_name__(self.__class__, name)
        return adapter_attribute_instance

    def validate(self, owner_instance=None):
        super().validate()
        owner_instance = self
        user_defined_fields = {f[0] for f in self.get_adapter_fields()}
        for k, v in self._raw_data.items():
            if k in user_defined_fields:
                continue
            if type(v) not in self._mapping:
                raise AdapterValidationError("Key's '%s' type not allowed" % k)
            self._get_attribute_adapter_instance(k, v).validate(owner_instance)


class AdapterObjectFreeContentAttribute(AdapterObjectAttribute, AdapterCompounded):
    def __init__(self, mapping, **kwargs):
        super().__init__(**kwargs)
        self._mapping = mapping

    def _get_adapter_creation_base_classes(self):
        return (AdapterFreeContent,)

    def _get_adapter_instance_params(self, instance):
        kwargs = super()._get_adapter_instance_params(instance)
        kwargs.update({'mapping': self._mapping})
        return kwargs


class AdapterFreeTypeAttribute(AdapterAttribute):
    def __init__(self, mapping, **kwargs):
        kwargs.pop('data_type', None)
        super().__init__(data_type=object, **kwargs)
        self._mapping = mapping

    def __get__(self, instance, owner):
        pass

    def _get_attribute_adapter_instance(self, name, raw_value):
        adapter_attribute_instance = self._mapping[type(raw_value)]
        adapter_attribute_instance.__set_name__(self.__class__, name)
        return adapter_attribute_instance

class RelationshipItem(AdapterObjectAttribute):
    type = AdapterAttribute(data_type=str)
    id = AdapterAttribute(data_type=str)

attributes_mapping = {
    str: (AdapterAttribute(data_type=str))
}

relationship_mapping = {
    dict: (RelationshipItem(data_type=dict))
}

class AttributesObject(AdapterObjectFreeContentAttribute):
    hello = AdapterAttribute(data_type=int)


class JSONApi(BaseAdapter):
    type = AdapterAttribute(data_type=str)
    id = AdapterAttribute(data_type=str)
    attributes = AttributesObject(attributes_mapping, searchable=True, required=False)
    relationships = AdapterObjectFreeContentAttribute(relationship_mapping, searchable=True)


data = {
    "id": "1",
    "type": "Siema",
    "attributes": {
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
# TODO validate empty dict (required satisfied or not)