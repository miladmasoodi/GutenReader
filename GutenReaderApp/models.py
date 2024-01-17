from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from SiteScripts import BookParser
"""File field, Text field(contents of .txt), 
Meta - Title, Author, Language: Char fields(3) 
Chapters - titles, start and end(by char not lines) JSON field(2)
"""
# Create your models here.
class Book(models.Model):
    # Metadata
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    language = models.CharField(max_length=50)
    # Content Info
    full_text = models.TextField()
    # Chapter Info
    chapter_titles = models.JSONField(default=list)
    chapter_divisions = models.JSONField(default=list)

    def __str__(self):
        return self.title

class TextUpload(models.Model):
    txt_file = models.FileField(upload_to='/txt_files/')

    def __str__(self):
        return self.txt_file.name
@receiver(post_save, sender=TextUpload)  # uses signals
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        cur_txt_file = instance.txt_file
        result = BookParser.ParseFile(cur_txt_file)
        cur_txt_file.delete()


