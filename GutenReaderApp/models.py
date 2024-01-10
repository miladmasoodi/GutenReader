from django.db import models
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
    txt_file = models.FileField(upload_to='/txt_files/')
    # Chapter Info
    chapter_titles = models.JSONField(default=list)
    chapter_divisions = models.JSONField(default=list)

    def __str__(self):
        return self.title


