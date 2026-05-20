"""Публичный эндпоинт обратной связи.

Контракт: contracts/feedback/submit.json — POST /api/feedback (без auth).

Антиспам через django-ratelimit. На превышение поднимается Ratelimited,
который глобальный хендлер конвертит в 429 + shared/error.

ВНИМАНИЕ: без `from __future__ import annotations` — Ninja парсит сигнатуры
эндпоинтов на стадии импорта, отложенные аннотации ломают разрешение схем.
"""

from django.http import HttpRequest
from django_ratelimit.decorators import ratelimit
from ninja import Router

from .schemas import FeedbackSubmitRequest, FeedbackSubmitResponse
from .services import SUCCESS_MESSAGE, create_feedback

router = Router(tags=["Feedback"])


@router.post(
    "",
    response={201: FeedbackSubmitResponse},
    summary="Отправить обращение с формы обратной связи",
)
@ratelimit(key="ip", rate="5/h", method="POST", block=True)
def submit_feedback(request: HttpRequest, data: FeedbackSubmitRequest):
    feedback = create_feedback(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        message=data.message,
        request=request,
    )
    return 201, {"id": feedback.id, "message": SUCCESS_MESSAGE}
