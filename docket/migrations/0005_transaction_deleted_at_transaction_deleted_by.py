# Generated by Django 5.2.4 on 2025-07-17 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docket', '0004_casedetails_debtor_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='deleted_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
