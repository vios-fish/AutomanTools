# Generated by Django 3.0.4 on 2020-12-13 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('originals', '0003_remove_original_delete_flag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='original',
            name='size',
            field=models.BigIntegerField(),
        ),
    ]