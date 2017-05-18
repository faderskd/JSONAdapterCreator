import abc


class AdapterSearchable(metaclass=abc.ABCMeta):
    def __init__(self, searchable=False, **kwargs):
        self.__dict__['searchable'] = searchable

    @abc.abstractmethod
    def search_in_attributes(self, search_name, owner_instance):
        pass


class AdapterAliased(metaclass=abc.ABCMeta):
    def __init__(self, source_aliases=None, target_alias=None, **kwargs):
        self.__dict__['source_aliases'] = source_aliases if source_aliases else []
        self.__dict__['target_alias'] = target_alias

    @abc.abstractmethod
    def search_aliased_adapter(self, target_alias, owner_instance):
        pass


class AdapterInsertTarget(metaclass=abc.ABCMeta):
    def __init__(self, insertable=False, insert_type=object, **kwargs):
        self.__dict__['insertable'] = insertable
        self.__dict__['insert_type'] = insert_type

    @abc.abstractmethod
    def insert_value(self, key, value, owner_instance):
        pass