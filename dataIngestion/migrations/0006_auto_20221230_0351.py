# Generated by Django 2.2 on 2022-12-30 03:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataIngestion', '0005_alter_upload_dataset_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='importSources',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='upload_dataset',
            name='name',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='upload_dataset',
            name='import_sources',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sources', to='dataIngestion.importSources'),
        ),
    ]
