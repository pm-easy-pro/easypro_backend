from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_user_otp_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="agent_pin_hash",
            field=models.CharField(blank=True, default="", max_length=128),
        ),
        migrations.AddField(
            model_name="user",
            name="agent_pin_set_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="agent_pin_failed_attempts",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="agent_pin_locked_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="phoneotp",
            name="purpose",
            field=models.CharField(
                choices=[
                    ("login", "Нэвтрэх OTP"),
                    ("agent_pin_setup", "Agent PIN тохиргоо"),
                    ("agent_pin_reset", "Agent PIN reset"),
                ],
                db_index=True,
                default="login",
                max_length=32,
            ),
        ),
    ]
