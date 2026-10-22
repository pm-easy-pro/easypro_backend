from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0007_property_visibility_scopes"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="contact_phone",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Энэ зар дээр харагдах утас",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="has_object",
            field=models.BooleanField(
                default=False,
                help_text="Газар дээр объект (барилга) байгаа эсэх",
            ),
        ),
    ]
