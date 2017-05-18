import schema
import copy

example_user_data = {
    'username': 'faderskd',
    'first_name': 'Daniel',
    'email': 'daniel@op.pl',
    'is_active': True,
    'birth_date': '01.01.2000'
}


class UserSchema(schema.Schema):
    username = schema.SchemaAttribute(str)
    first_name = schema.SchemaAttribute(str, required=False, required_with=['birth_date'])
    email = schema.SchemaAttribute(str)
    is_active = schema.SchemaAttribute(bool)
    birth_date = schema.SchemaAttribute(str, required=False)


class Settings(schema.SchemaCompoundedAttribute):
    profile_color = schema.SchemaAttribute(str)
    stay_logged = schema.SchemaAttribute(bool)


class ProfileSchema(schema.SchemaCompoundedAttribute):
    last_logged = schema.SchemaAttribute(str)
    settings = Settings()


class UserCompoundedSchema(UserSchema):
    profile = ProfileSchema()


example_compounded_user_data = example_user_data.copy()
profile_data = {
    'profile': {
        'last_logged': 'yesterday',
        'settings': {
            'profile_color': 'green',
            'stay_logged': True
        }
    }
}
example_compounded_user_data.update(profile_data)


class UserAppearance(schema.SchemaCompoundedAttribute):
    height = schema.SchemaAttribute(data_type=str)
    age = schema.SchemaAttribute(data_type=int)


user_attribute_mapping = {
    str: schema.SchemaAttribute(data_type=str),
    dict: UserAppearance(data_type=dict)
}

example_free_content_user_data = copy.deepcopy(example_compounded_user_data)
attributes_data = {
    'attributes': {
        'surname': 'Kolik',
        'job': 'Programmer',
        'appearance': {
            'height': '174cm',
            'age': 22
        }
    }
}
example_free_content_user_data.update(attributes_data)


class UserWithFreeContentAttributesSchema(UserCompoundedSchema):
    attributes = schema.SchemaFreeContentCompoundedAttribute(mapping=user_attribute_mapping)


user_type_mapping = {
    str: schema.SchemaAttribute(data_type=str),
    dict: schema.SchemaFreeContentCompoundedAttribute(mapping=user_attribute_mapping)

}
example_free_type_user_data = copy.deepcopy(example_free_content_user_data)


class UserWithFreeTypeAttributeSchema(UserCompoundedSchema):
    attributes = schema.SchemaFreeTypeAttribute(mapping=user_type_mapping)


class Post(schema.SchemaCompoundedAttribute):
    title = schema.SchemaAttribute(data_type=str)
    tags = schema.SchemaCollectionAttribute(inner_attribute=schema.SchemaAttribute(data_type=str))


example_collection_user_data = copy.deepcopy(example_free_type_user_data)
posts_data = {'posts': [
        {'title': 'How inheritance work in python', 'tags': ['Python', 'Inheritance']},
        {'title': 'Most popular languages in 2017', 'tags': ['Programming', 'Programming Languages']},
    ]
}
example_collection_user_data.update(posts_data)


class UserWithCollectionAttributeSchema(UserWithFreeTypeAttributeSchema):
    posts = schema.SchemaCollectionAttribute(inner_attribute=Post())
