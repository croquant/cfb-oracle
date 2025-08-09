from django.test import TestCase

from core.models.venue import Venue


class VenueModelTests(TestCase):
    def test_str_returns_name_and_location(self):
        """``__str__`` returns '<name> (<city>, <state>)'."""
        venue = Venue.objects.create(
            name="Memorial Stadium", city="Athens", state="GA"
        )
        self.assertEqual(str(venue), "Memorial Stadium (Athens, GA)")

    def test_meta_options(self):
        """Model meta options specify ordering and verbose names."""
        self.assertEqual(Venue._meta.ordering, ["name"])
        self.assertEqual(Venue._meta.verbose_name, "venue")
        self.assertEqual(Venue._meta.verbose_name_plural, "venues")
