from django.db import migrations, models


def migrate_view_direction_to_list(apps, schema_editor):
    Property = apps.get_model("properties", "Property")
    for prop in Property.objects.all().iterator():
        old = getattr(prop, "view_direction", "") or ""
        if old:
            prop.view_directions = [old]
            prop.save(update_fields=["view_directions"])


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0005_property_land_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="view_directions",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Цонхны харагдац — олон чиглэл (north, south, …)",
            ),
        ),
        migrations.RunPython(migrate_view_direction_to_list, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="property",
            name="view_direction",
        ),
    ]
