import os
import re
from mimetypes import guess_type
from zipfile import ZipFile, is_zipfile

from django.core.files import File
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from SiteScripts import HTMLBookParser

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

    # Content
    #default cover image isn't indivdualy saved in DB
    book_cover = models.ImageField(upload_to="book_covers/", blank=True, null=True)
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

def has_dir(zip_file):
    info_list = zip_file.infolist()
    for info in info_list:
        if info.is_dir():
            return True
    return False
def extract_path(zip_file, regex_pattern):
    name_list = zip_file.namelist()
    match_count = 0
    match = ""
    print(name_list)
    for name in name_list:
        regex_match = re.search(regex_pattern, name)
        if regex_match is not None:
            print(name)
            match_count += 1
            match = name
    if match_count != 1:
        raise Exception("Ambiguous Match Count: " + str(match_count))
    zip_info = zip_file.getinfo(match)
    zip_info.filename = os.path.basename(zip_info.filename)
    path = zip_file.extract(zip_info)
    return path


@receiver(post_save, sender=TextUpload)  # uses signals
def parse_book(sender, instance, created, **kwargs):
    if created:
        cover_path = ""
        cur_book_file = instance.book_file
        html_path = cur_book_file.path
        context_type = guess_type(html_path)[0]
        is_zip = context_type == "application/zip" or context_type == "application/x-zip-compressed"
        is_html = context_type == "text/html"
        if not (is_html or (is_zip and is_zipfile(html_path))):
            raise Exception("HTML or ZIP Uploads Only: " + str(context_type))
        if is_zip:
            cover_regex = r"\S*cover\.\w+"
            html_regex = r"\S*\.htm\w?"

            with ZipFile(html_path, 'r') as zip:
                zip_valid = zip.testzip() is None
                if not zip_valid:
                    raise Exception("ZIP not valid")
                cover_path = extract_path(zip, cover_regex)
                html_path = extract_path(zip, html_regex)

        f = open(html_path, "r", encoding='utf-8')
        try:
            result = HTMLBookParser.parse_html_file(f)
        except Exception as e:
            print("Failed to Parse, \nException: " + str(e))
        else:
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
            if cover_path != "":
                with open(cover_path, 'rb') as f:
                    image_file = File(f)
                    new_book.book_cover.save(str(result["pg_id"]) + "cover.png", image_file, save=True)
            new_book.save()
            add_subject_tags(new_book, result["meta_tags"])
        f.close()

        os.remove(html_path)
        instance.delete()


def add_subject_tags(book, subject_tags: list):
    for tag in subject_tags:
        tag_model, tag_created = SubjectTag.objects.get_or_create(content=tag)
        tag_model.books.add(book)
        tag_model.save()
        if tag_created:
            print("NEW Tag: " + str(tag_model))
