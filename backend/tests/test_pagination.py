"""Tests for pagination helpers."""
from __future__ import annotations

from backend.app.pagination import Page, PageParams


def test_page_params_defaults():
    params = PageParams()
    assert params.skip == 0
    assert params.limit == 50


def test_page_params_custom():
    params = PageParams(skip=10, limit=25)
    assert params.skip == 10
    assert params.limit == 25


def test_page_of_with_total():
    items = list(range(10))
    page = Page.of(items, skip=0, limit=10, total=50)
    assert page.items == items
    assert page.total == 50
    assert page.has_more is True
    assert page.skip == 0
    assert page.limit == 10


def test_page_of_last_page():
    items = list(range(5))
    page = Page.of(items, skip=45, limit=10, total=50)
    assert page.has_more is False


def test_page_of_no_total():
    items = [1, 2, 3]
    page = Page.of(items, skip=0, limit=50)
    assert page.total is None
    assert page.has_more is False
