# Generated by Django 4.0.1 on 2022-01-25 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_alter_constraint_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='participant',
            options={'verbose_name': 'Участник проекта', 'verbose_name_plural': 'Участники проектов'},
        ),
        migrations.AlterModelOptions(
            name='project',
            options={'verbose_name': 'Типовой проект', 'verbose_name_plural': 'Типовые проекты'},
        ),
        migrations.AlterField(
            model_name='participant',
            name='name',
            field=models.CharField(max_length=32, verbose_name='Имя (и фамилия)'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='tg_username',
            field=models.CharField(help_text='без символа @', max_length=32, verbose_name='Ник в Telegram'),
        ),
    ]