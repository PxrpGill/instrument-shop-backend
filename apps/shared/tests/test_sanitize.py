"""Тесты HTML sanitize: whitelist работает, опасные теги вырезаются."""

from __future__ import annotations

from apps.shared.services.sanitize import sanitize_html


def test_sanitize_empty_input_returns_empty_string():
    assert sanitize_html("") == ""
    assert sanitize_html(None) == ""


def test_sanitize_keeps_allowed_tags():
    html = "<p>Текст <strong>важный</strong></p><h2>Заголовок</h2>"
    result = sanitize_html(html)
    assert "<p>" in result
    assert "<strong>" in result
    assert "<h2>" in result


def test_sanitize_strips_script_tag():
    html = "<p>ok</p><script>alert('xss')</script>"
    result = sanitize_html(html)
    # bleach убирает сам тег <script>; его содержимое остаётся как plain text,
    # что XSS-безопасно (текст не исполняется браузером). Главное — нет тега.
    assert "<script" not in result.lower()
    assert "</script>" not in result.lower()
    assert "<p>ok</p>" in result


def test_sanitize_strips_event_handlers():
    html = '<a href="https://example.com" onclick="alert(1)">click</a>'
    result = sanitize_html(html)
    assert "onclick" not in result
    assert 'href="https://example.com"' in result


def test_sanitize_strips_javascript_protocol():
    html = '<a href="javascript:alert(1)">x</a>'
    result = sanitize_html(html)
    assert "javascript:" not in result


def test_sanitize_keeps_safe_link():
    html = '<a href="mailto:test@example.com">mail</a>'
    result = sanitize_html(html)
    assert "mailto:test@example.com" in result
