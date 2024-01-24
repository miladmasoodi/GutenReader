# Generated by Django 5.0 on 2024-01-18 00:59

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('author', models.CharField(max_length=100)),
                ('language', models.CharField(max_length=50)),
                ('full_text', models.TextField()),
                ('chapter_titles', models.JSONField(default=list)),
                ('chapter_divisions', models.JSONField(default=list)),
            ],
        ),
        migrations.CreateModel(
            name='TextUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('txt_file', models.FileField(upload_to='txt_files/')),
            ],
        ),
    ]
