# Generated by Django 5.1.3 on 2024-11-21 23:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carriers', '0002_rename_patent_carrier_dni_carrier_email_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patent',
            name='id_carrier',
        ),
        migrations.RemoveField(
            model_name='remito',
            name='id_paten',
        ),
        migrations.DeleteModel(
            name='Carrier',
        ),
        migrations.DeleteModel(
            name='Patent',
        ),
        migrations.DeleteModel(
            name='Remito',
        ),
    ]