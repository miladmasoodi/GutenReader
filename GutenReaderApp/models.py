from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from SiteScripts import HTMLBookParser
from mimetypes import guess_type
import os

"""File field, Text field(contents of .txt), 
Meta - Title, Author, Language: Char fields(3) 
Chapters - titles, start and end(by char not lines) JSON field(2)
"""


class Book(models.Model):
    # Metadata
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    language = models.CharField(max_length=50)
    translater = models.CharField(max_length=100, default="", blank=True)
    view_count = models.IntegerField(default=0)
    do_recommend_count = models.IntegerField(default=0)
    do_not_recommend_count = models.IntegerField(default=0)
    date_added = models.DateTimeField(default=timezone.now)
    project_gutenberg_id = models.IntegerField(default=-1)

    # Content Info
    full_text = models.TextField()
    # Chapter Info
    chapter_titles = models.JSONField(default=list)
    chapter_divisions = models.JSONField(default=list)
    section_indices = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.title


class TextUpload(models.Model):
    book_file = models.FileField(upload_to='book_files/')


class SubjectTag(models.Model):
    content = models.CharField(max_length=40)
    books = models.ManyToManyField(Book)

    def __str__(self):
        return self.content


@receiver(post_save, sender=TextUpload)  # uses signals
def parse_book(sender, instance, created, **kwargs):
    if created:
        cur_book_file = instance.book_file
        context_type = guess_type(cur_book_file.path)[0]
        if context_type != "text/html":
            raise Exception("HTML Uploads Only: " + str(context_type))

        f = open(cur_book_file.path, "r", encoding='utf-8')
        result = HTMLBookParser.parse_html_file(f)
        f.close()

        new_book = Book(title=result["meta_values"][0],
                        author=result["meta_values"][1],
                        language=result["meta_values"][2],
                        translater=result["meta_values"][3],
                        full_text=result["full_text"],
                        chapter_titles=result["chapter_titles"],
                        chapter_divisions=result["chapter_divisions"],
                        section_indices=result["section_indices"],
                        project_gutenberg_id=result["pg_id"])
        new_book.save()
        add_subject_tags(new_book, result["meta_tags"])
        os.remove(cur_book_file.path)
        instance.delete()


def add_subject_tags(book, subject_tags: list):
    for tag in subject_tags:
        tag_model, tag_bool = SubjectTag.objects.get_or_create(content=tag)
        tag_model.books.add(book)
        tag_model.save()
        if tag_bool:
            print("NEW Tag: " + str(tag_model))
