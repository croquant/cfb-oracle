from django.test import TestCase

from core.models.conference import Conference


class ConferenceModelTests(TestCase):
    def test_str_returns_name(self):
        """``__str__`` returns the conference name."""
        conf = Conference.objects.create(name="Big Ten")
        self.assertEqual(str(conf), "Big Ten")

    def test_save_generates_unique_slugs(self):
        """Saving conferences with the same name generates unique slugs."""
        c1 = Conference.objects.create(name="Big Ten")
        c2 = Conference.objects.create(name="Big Ten")
        self.assertEqual(c1.slug, "big-ten")
        self.assertEqual(c2.slug, "big-ten-1")

    def test_save_overwrites_invalid_slug(self):
        """A provided slug that doesn't contain the name is replaced."""
        conf = Conference.objects.create(name="Mid-American", slug="invalid")
        self.assertEqual(conf.slug, "mid-american")

    def test_save_preserves_valid_slug(self):
        """A slug containing the slugified name remains unchanged on save."""
        conf = Conference.objects.create(
            name="Mountain West", slug="mountain-west-custom"
        )
        original_slug = conf.slug
        conf.save()
        self.assertEqual(conf.slug, original_slug)
