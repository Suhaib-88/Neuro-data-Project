# Generated by Django 2.2 on 2022-12-03 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataProcessing', '0003_auto_20221203_1208'),
    ]

    operations = [
        migrations.AlterField(
            model_name='settarget_column',
            name='set_target_column',
            field=models.CharField(choices=[('hi', 'hi'), ('hello', 'hello')], max_length=30),
        ),
    ]