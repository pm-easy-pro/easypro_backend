from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0003_property_detail_specs"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="payment_terms",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
