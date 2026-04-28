# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_user_daily_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='group_night_events',
            field=models.BooleanField(default=False, help_text='Group events by night (8 PM - 8 AM) instead of calendar day'),
        ),
    ]
