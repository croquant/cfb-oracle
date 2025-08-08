from django.test import TestCase

from core.models.conference import Conference


class ConferenceModelTests(TestCase):
    def test_conference_str(self):
        """``__str__`` should return the conference name."""
        conf = Conference.objects.create(name="Test Conference")
        self.assertEqual(str(conf), "Test Conference")

    def test_save_generates_unique_slugs(self):
        """Saving with duplicate names should append numeric suffixes."""
        c1 = Conference.objects.create(name="Slug League")
        c2 = Conference.objects.create(name="Slug League")
        c3 = Conference.objects.create(name="Slug League")

        self.assertEqual(c1.slug, "slug-league")
        self.assertEqual(c2.slug, "slug-league-1")
        self.assertEqual(c3.slug, "slug-league-2")

    def test_save_preserves_existing_slug(self):
        """A valid, existing slug should remain unchanged on save."""
        conf = Conference.objects.create(name="Valid Slug", slug="valid-slug")
        original = conf.slug
        conf.save()
        self.assertEqual(conf.slug, original)
