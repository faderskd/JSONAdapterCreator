import schema


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
