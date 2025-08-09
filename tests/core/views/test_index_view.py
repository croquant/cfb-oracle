from django.test import TestCase
from django.urls import reverse


class IndexViewTests(TestCase):
    def test_index_view_renders_template(self):
        """The index view should return the index template."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
