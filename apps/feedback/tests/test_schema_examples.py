from apps.feedback.schemas import FeedbackSubmitResponse


def test_feedback_submit_response_has_example():
    assert "example" in FeedbackSubmitResponse.model_json_schema()
