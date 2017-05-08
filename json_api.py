from base import AdapterAttribute
from mixture import BaseAdapter, AdapterObjectAttribute, AdapterObjectFreeContentAttribute, AdapterFreeTypeAttribute


class LinksObject(AdapterObjectAttribute):
    self = AdapterAttribute(str, target_alias='dupa')
    related = AdapterAttribute(str, required=False)


attributes_mapping = {
    str: AdapterAttribute(str)
}


class RelationshipItemData(AdapterObjectAttribute):
    type = AdapterAttribute(str)
    id = AdapterAttribute(str)


class RelationshipItem(AdapterObjectAttribute):
    links = LinksObject(required=False)
    data = RelationshipItemData(searchable=True, insertable=True)


relationships_type_mapping = {
    dict: RelationshipItem()
}


class MainDataItem(AdapterObjectAttribute):
    type = AdapterAttribute(str)
    id = AdapterAttribute(str)
    attributes = AdapterObjectFreeContentAttribute(attributes_mapping, required=False, searchable=True, insertable=True)
    links = LinksObject(required=False)
    relationships = AdapterObjectFreeContentAttribute(relationships_type_mapping, required=False, searchable=True, target_alias='relations')


main_data_type_mapping = {
    dict: MainDataItem(searchable=True, insertable=True),
    # list: Collection()
}


class JSONApiAdapter(BaseAdapter):
    def __init__(self, raw_data, **kwargs):
        super().__init__(raw_data, source_aliases=['relations', 'dupa'], **kwargs)

    data = AdapterFreeTypeAttribute(main_data_type_mapping, searchable=True, insertable=True)
    #included

raw_data = {
    "data": {
        "type": "articles",
        "id": "1",
        "attributes": {
            "title": "JSON API paints my bikeshed!",
        },
        "links": {
            "self": "http://example.com/articles/1"
        },
        "relationships": {
            "author": {
                "links": {
                    "self": "http://example.com/articles/1/relationships/author",
                    "related": "http://example.com/articles/1/author"
                },
                "data": {"type": "people", "id": "9"}
            },
            "comments": {
                "links": {
                    "self": "http://example.com/articles/1/relationships/comments",
                    "related": "http://example.com/articles/1/comments"
                },
                "data": {"type": "comments", "id": "5", },
            }
        }
    }
}

j = JSONApiAdapter(raw_data)
j.validate()