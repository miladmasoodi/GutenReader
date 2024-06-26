# Generated by Django 5.0 on 2024-04-17 17:48

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GutenReaderApp', '0002_book_recommend_counts_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='date_added',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='book',
            name='project_gutenberg_id',
            field=models.IntegerField(default=-1),
        ),
    ]
