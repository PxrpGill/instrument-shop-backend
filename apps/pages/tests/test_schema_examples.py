from apps.pages.schemas import BannerPageOut, FeedbackPageOut, HomePageOut, LegalDocumentOut


def test_home_page_out_has_example():
    assert "example" in HomePageOut.model_json_schema()


def test_banner_page_out_has_example():
    assert "example" in BannerPageOut.model_json_schema()


def test_feedback_page_out_has_example():
    assert "example" in FeedbackPageOut.model_json_schema()


def test_legal_document_out_has_example():
    assert "example" in LegalDocumentOut.model_json_schema()
