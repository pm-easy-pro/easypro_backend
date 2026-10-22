from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_agent_pin_and_otp_purpose"),
    ]

    operations = [
        migrations.AddField(
            model_name="agent",
            name="contact_phones",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Нэвтрэх дугаараас гадна зар дээр сонгох нэмэлт дугаарууд",
            ),
        ),
    ]
