import schema


class LinksObject(schema.SchemaCompoundedAttribute):
    self = schema.SchemaAttribute(data_type=str)


class RelationshipLinksObject(LinksObject):
    related = schema.SchemaAttribute(data_type=str)


attributes_mapping = {
    str: schema.SchemaAttribute(data_type=str)
}


class RelationshipItemData(schema.SchemaCompoundedAttribute):
    type = schema.SchemaAttribute(data_type=str)
    id = schema.SchemaAttribute(data_type=str)


relationships_data_type_mapping = {
    dict: RelationshipItemData(),
    list: schema.SchemaCollectionAttribute(inner_attribute=RelationshipItemData())
}


class RelationshipItem(schema.SchemaCompoundedAttribute):
    links = RelationshipLinksObject(required=False)
    data = schema.SchemaFreeTypeAttribute(mapping=relationships_data_type_mapping)


relationships_type_mapping = {
    dict: RelationshipItem()
}


class MainDataItem(schema.SchemaCompoundedAttribute):
    type = schema.SchemaAttribute(data_type=str)
    id = schema.SchemaAttribute(data_type=str)
    attributes = schema.SchemaFreeContentCompoundedAttribute(attributes_mapping, required=False)
    links = LinksObject(required=False)
    relationships = schema.SchemaFreeContentCompoundedAttribute(relationships_type_mapping, required=False)


main_data_type_mapping = {
    dict: MainDataItem(),
    list: schema.SchemaCollectionAttribute(inner_attribute=MainDataItem())
}


class JSONApiSchema(schema.Schema):
    data = schema.SchemaFreeTypeAttribute(mapping=main_data_type_mapping)
    #included


raw_data = {
    "data": [{
        "type": "articles",
        "id": "1",
        "attributes": {
            "title": "JSON API paints my bikeshed!"
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
                "data": [
                    {"type": "comments", "id": "5"},
                    {"tyjpe": "comments", "id": "12"}
                ]
            }
        }
    }]
}

j = JSONApiSchema()
validator = j.get_validator()
validator.validate(raw_data)