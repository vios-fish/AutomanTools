# Generated by Django 2.2.2 on 2020-01-22 06:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_remove_klassklassset_delete_flag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='klassset',
            name='delete_flag',
        ),
        migrations.RemoveField(
            model_name='projects',
            name='delete_flag',
        ),
    ]
