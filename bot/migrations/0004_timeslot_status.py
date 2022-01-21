# Generated by Django 4.0.1 on 2022-01-21 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bot", "0003_remove_productmanager_surname_remove_student_surname_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="timeslot",
            name="status",
            field=models.CharField(
                choices=[
                    ("BUSY", "Временной слот занят"),
                    ("FREE", "Временной слот свободен"),
                ],
                default="FREE",
                max_length=4,
                verbose_name="Статус",
            ),
        ),
    ]
