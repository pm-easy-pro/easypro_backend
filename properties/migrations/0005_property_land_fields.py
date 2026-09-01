from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0004_property_payment_terms"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="land_contract_end",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="property",
            name="land_contract_start",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="property",
            name="land_right_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("ownership", "Өмчлөх"),
                    ("possession", "Эзэмших"),
                    ("use", "Ашиглах"),
                ],
                db_index=True,
                default="",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="land_use_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("service_apartment", "Үйлчилгээтэй орон сууц"),
                    ("household", "Аж, ахуйн"),
                    ("residential_yard", "Гэр, орон сууц хашааны газар"),
                    ("private_residence", "Амины орон сууц"),
                    ("other", "Бусад"),
                ],
                db_index=True,
                default="",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="parcel_number",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
