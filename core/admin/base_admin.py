from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    fieldsets = tuple(
        (
            name,
            {
                **opts,
                "classes": opts.get("classes", ()) + ("tab",),
            },
        )
        for name, opts in BaseUserAdmin.fieldsets
    )
    add_fieldsets = tuple(
        (
            name,
            {
                **opts,
                "classes": opts.get("classes", ()) + ("tab",),
            },
        )
        for name, opts in BaseUserAdmin.add_fieldsets
    )


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    fieldsets = (
        (
            "Group Info",
            {
                "fields": ("name",),
                "classes": ("tab",),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("permissions",),
                "classes": ("tab",),
            },
        ),
    )
