"""Тесты пагинации: edge-кейсы (пустой qs, page > total, clamp per_page)."""

from __future__ import annotations

import pytest

from apps.shared.utils.pagination import MAX_PER_PAGE, paginate
from apps.users.models import Customer


@pytest.mark.django_db
def test_paginate_empty_queryset_returns_zero_meta():
    items, meta = paginate(Customer.objects.all(), page=1, per_page=10)
    assert items == []
    assert meta == {"page": 1, "per_page": 10, "total_pages": 0, "total_items": 0}


@pytest.mark.django_db
def test_paginate_returns_correct_meta(customer_factory):
    for i in range(5):
        customer_factory(email=f"u{i}@example.com")

    items, meta = paginate(Customer.objects.all(), page=1, per_page=2)
    assert len(items) == 2
    assert meta == {"page": 1, "per_page": 2, "total_pages": 3, "total_items": 5}


@pytest.mark.django_db
def test_paginate_page_beyond_total_returns_empty_items(customer_factory):
    customer_factory(email="a@example.com")

    items, meta = paginate(Customer.objects.all(), page=99, per_page=10)
    assert items == []
    assert meta["total_items"] == 1


def test_paginate_clamps_per_page_above_max():
    from django.db.models.query import QuerySet
    qs = Customer.objects.none()
    _, meta = paginate(qs, page=1, per_page=999)
    assert meta["per_page"] == MAX_PER_PAGE


def test_paginate_normalizes_negative_page():
    qs = Customer.objects.none()
    _, meta = paginate(qs, page=-5, per_page=10)
    assert meta["page"] == 1
