# Generated by Django 2.2 on 2022-12-03 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='target_column',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_target_column', models.CharField(choices=[('PassengerId', 'PassengerId'), ('Survived', 'Survived'), ('Pclass', 'Pclass'), ('Name', 'Name'), ('Sex', 'Sex'), ('Age', 'Age'), ('SibSp', 'SibSp'), ('Parch', 'Parch'), ('Ticket', 'Ticket'), ('Fare', 'Fare'), ('Cabin', 'Cabin'), ('Embarked', 'Embarked')], max_length=30)),
            ],
        ),
    ]
