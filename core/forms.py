from django import forms
from django.utils.safestring import mark_safe

from core.models.team import Team


class ColorPreviewWidget(forms.TextInput):
    """TextInput widget that displays a color picker with preview box."""

    input_type = "color"

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs.setdefault("id", f"id_{name}")
        preview_id = f"{attrs['id']}_preview"
        attrs["data-color-preview"] = preview_id
        html = super().render(name, value, attrs, renderer)
        preview_html = (
            f'<span id="{preview_id}" '
            'class="inline-block w-5 h-5 ml-2 border align-middle"></span>'
        )
        return mark_safe(html + preview_html)


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = "__all__"
        widgets = {
            "color": ColorPreviewWidget(),
            "alternate_color": ColorPreviewWidget(),
        }

    class Media:
        js = ["js/color_preview.js"]
