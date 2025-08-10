"""Tests for the index view."""

from django.test import TestCase
from django.urls import reverse


class IndexViewTests(TestCase):
    """Index view tests."""

    def test_index_view_renders_template(self) -> None:
        """The index view should return the index template."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
