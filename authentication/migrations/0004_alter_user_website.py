# Generated by Django 5.2.4 on 2025-07-25 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_alter_user_website'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='website',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
