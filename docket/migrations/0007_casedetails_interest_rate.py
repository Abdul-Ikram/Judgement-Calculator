# Generated by Django 5.2.4 on 2025-07-20 20:48

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('docket', '0006_casedetails_is_ended'),
    ]

    operations = [
        migrations.AddField(
            model_name='casedetails',
            name='interest_Rate',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12),
        ),
    ]
