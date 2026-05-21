from apps.users.api.auth_schemas import AuthResponse, MessageResponse, TokenPair, UserSchema


def test_user_schema_has_example():
    schema = UserSchema.model_json_schema()
    assert "example" in schema


def test_token_pair_has_example():
    schema = TokenPair.model_json_schema()
    assert "example" in schema


def test_auth_response_has_example():
    schema = AuthResponse.model_json_schema()
    assert "example" in schema


def test_message_response_has_example():
    schema = MessageResponse.model_json_schema()
    assert "example" in schema
