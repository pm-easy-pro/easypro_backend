from django.db import migrations, models


def set_public_visibility(apps, schema_editor):
    Property = apps.get_model("properties", "Property")
    for prop in Property.objects.all().iterator():
        scopes = prop.visibility_scopes
        if not scopes:
            prop.visibility_scopes = ["public"]
            prop.save(update_fields=["visibility_scopes"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0006_property_view_directions"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="visibility_scopes",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="public | company | network — олон сонголт зөвшөөрнө",
            ),
        ),
        migrations.RunPython(set_public_visibility, noop_reverse),
    ]
