from apps.news.schemas import NewsListResponse, NewsSingleResponse


def test_news_list_response_has_example():
    assert "example" in NewsListResponse.model_json_schema()


def test_news_single_response_has_example():
    assert "example" in NewsSingleResponse.model_json_schema()
