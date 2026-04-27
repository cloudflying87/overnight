# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_timezone'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='daily_email_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='daily_email_time',
            field=models.TimeField(default='07:00:00', help_text='Time to send daily summary email'),
        ),
        migrations.AddField(
            model_name='user',
            name='daily_email_recipients',
            field=models.TextField(blank=True, help_text='Comma-separated email addresses'),
        ),
    ]
