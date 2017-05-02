from base import AdapterAttribute
from mixture import BaseAdapter, AdapterObjectAttribute, AdapterObjectFreeContentAttribute, AdapterFreeTypeAttribute


class LinksObject(AdapterObjectAttribute):
    self = AdapterAttribute(str)
    related = AdapterAttribute(str, required=False)


attributes_mapping = {
    str: AdapterAttribute(str)
}


class RelationshipItemData(AdapterObjectAttribute):
    type = AdapterAttribute(str)
    id = AdapterAttribute(str)


class RelationshipItem(AdapterObjectAttribute):
    links = LinksObject(required=False)
    data = RelationshipItemData(searchable=True, insert=True)


relationships_type_mapping = {
    dict: RelationshipItem()
}


class MainDataItem(AdapterObjectAttribute):
    type = AdapterAttribute(str)
    id = AdapterAttribute(str)
    attributes = AdapterObjectFreeContentAttribute(attributes_mapping, required=False, searchable=True, insert=True, insert_type=str)
    links = LinksObject(required=False)
    relationships = AdapterObjectFreeContentAttribute(relationships_type_mapping, required=False, searchable=True, insert=True, insert_type=dict)
    # included


main_data_type_mapping = {
    dict: MainDataItem(searchable=True),
    # list: Collection()
}

class JSONApiAdapter(BaseAdapter):
    data = AdapterFreeTypeAttribute(main_data_type_mapping, searchable=True, insert=True)

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