from django import forms

from core.models.team import Team
from core.models.venue import Venue


class TeamAdminForm(forms.ModelForm):
    location_name = forms.CharField(max_length=200, required=False)
    location_city = forms.CharField(max_length=100, required=False)
    location_state = forms.CharField(max_length=100, required=False)
    location_zip_code = forms.CharField(max_length=20, required=False)
    location_country_code = forms.CharField(max_length=3, required=False)
    location_timezone = forms.CharField(max_length=50, required=False)
    location_latitude = forms.FloatField(required=False)
    location_longitude = forms.FloatField(required=False)
    location_elevation = forms.FloatField(required=False)
    location_capacity = forms.IntegerField(required=False)
    location_construction_year = forms.IntegerField(required=False)
    location_grass = forms.BooleanField(required=False)
    location_dome = forms.BooleanField(required=False)

    class Meta:
        model = Team
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        venue = self.instance.location
        if venue:
            self.fields['location_name'].initial = venue.name
            self.fields['location_city'].initial = venue.city
            self.fields['location_state'].initial = venue.state
            self.fields['location_zip_code'].initial = venue.zip_code
            self.fields['location_country_code'].initial = venue.country_code
            self.fields['location_timezone'].initial = venue.timezone
            self.fields['location_latitude'].initial = venue.latitude
            self.fields['location_longitude'].initial = venue.longitude
            self.fields['location_elevation'].initial = venue.elevation
            self.fields['location_capacity'].initial = venue.capacity
            self.fields['location_construction_year'].initial = venue.construction_year
            self.fields['location_grass'].initial = venue.grass
            self.fields['location_dome'].initial = venue.dome

    def save(self, commit=True):
        venue = self.instance.location or Venue()
        venue.name = self.cleaned_data.get('location_name')
        venue.city = self.cleaned_data.get('location_city')
        venue.state = self.cleaned_data.get('location_state')
        venue.zip_code = self.cleaned_data.get('location_zip_code')
        venue.country_code = self.cleaned_data.get('location_country_code')
        venue.timezone = self.cleaned_data.get('location_timezone')
        venue.latitude = self.cleaned_data.get('location_latitude')
        venue.longitude = self.cleaned_data.get('location_longitude')
        venue.elevation = self.cleaned_data.get('location_elevation')
        venue.capacity = self.cleaned_data.get('location_capacity')
        venue.construction_year = self.cleaned_data.get('location_construction_year')
        venue.grass = self.cleaned_data.get('location_grass')
        venue.dome = self.cleaned_data.get('location_dome')
        venue.save()
        self.instance.location = venue
        return super().save(commit=commit)
