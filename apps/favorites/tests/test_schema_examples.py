from apps.favorites.schemas import FavoriteToggleResponse, FavoritesListResponse


def test_favorites_list_response_has_example():
    assert "example" in FavoritesListResponse.model_json_schema()


def test_favorite_toggle_response_has_example():
    assert "example" in FavoriteToggleResponse.model_json_schema()
