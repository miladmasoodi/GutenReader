import os
import re
from mimetypes import guess_type
from zipfile import ZipFile, is_zipfile
from django.core.cache import cache
from django.core.files import File
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from SiteScripts import HTMLBookParser


def cover_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/book_covers/{1st digit of 6 digit pg_id}/{2nd---}/{3nd---}/{filename}
    pgid = instance.project_gutenberg_id
    formatted_pgid = str(pgid).zfill(6)
    print(formatted_pgid)
    return "book_covers/{0}/{1}/{2}/{3}".format(formatted_pgid[0], formatted_pgid[1], formatted_pgid[2], filename)


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
    """
    If a new Book model is being added with a previously existing/used PG_ID: 
    the new model will copy/keep certain metadata (view_count, do_recommend_count, do_not_recommend_count) 
    from the existing model before deleting the older one
    """
    project_gutenberg_id = models.IntegerField(default=-1)

    """
    Expected to always be True, meaning that the copyright status was listed as: "Public domain in the USA." 
    Stored as verification that copyright status was checked
    """
    verified_public_domain = models.BooleanField(default=False)

    # Content
    # default cover image isn't individually saved in DB
    book_cover = models.ImageField(upload_to=cover_directory_path, blank=True, null=True)
    full_text = models.TextField()
    # Chapter Info
    chapter_titles = models.JSONField(default=list)
    chapter_divisions = models.JSONField(default=list)
    section_indices = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("index", kwargs={"book_id": self.pk})


class TextUpload(models.Model):  # for development/testing only, not accessible to users
    book_file = models.FileField(upload_to='book_files/')


@receiver(post_save, sender=TextUpload)  # uses signals
def process_upload(sender, instance, created, **kwargs):
    if created:
        cur_book_file = instance.book_file
        book_file_path = cur_book_file.path
        handle_create_book_from_path(book_file_path)
        instance.delete()


class SubjectTag(models.Model):
    content = models.CharField(max_length=40)
    books = models.ManyToManyField(Book)
    num_books = models.IntegerField(default=0)

    def __str__(self):
        return self.content

    def get_absolute_url(self):
        return reverse("tag-index", kwargs={"tag_id": self.pk})


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
    for name in name_list:
        regex_match = re.search(regex_pattern, name)
        if regex_match is not None:
            match_count += 1
            match = name
    if match_count != 1:
        if match_count == 0:
            return ""
        else:
            raise Exception("Ambiguous Match Count: " + str(match_count))
    zip_info = zip_file.getinfo(match)
    zip_info.filename = os.path.basename(zip_info.filename)
    path = zip_file.extract(zip_info)
    return path


def create_book_from_path(book_file_path):
    cover_path = ""
    html_path = book_file_path
    context_type = guess_type(book_file_path)[0]
    is_zip = context_type == "application/zip" or context_type == "application/x-zip-compressed"
    is_html = context_type == "text/html"
    if not (is_html or (is_zip and is_zipfile(book_file_path))):
        raise Exception("HTML or ZIP Uploads Only: " + str(context_type))
    if is_zip:
        cover_regex = r"\S*cover\.\w+"
        html_regex = r"\S*\.htm\w?"

        with ZipFile(book_file_path, 'r') as zip:
            zip_valid = zip.testzip() is None
            if not zip_valid:
                raise Exception("ZIP not valid")
            cover_path = extract_path(zip, cover_regex)
            html_path = extract_path(zip, html_regex)

    html_file = open(html_path, "r", encoding='utf-8')
    try:
        result = HTMLBookParser.parse_html_file(html_file)
    except Exception as e:
        print("Failed to Parse, \nException: " + str(e))

    else:
        # if is_zip or is_html:
        #     result = HTMLBookParser.parse_html_file(f)
        view_count = 0
        rec_count = 0
        dn_rec_count = 0
        pg_id = result["pg_id"]
        book_copies = Book.objects.filter(project_gutenberg_id=pg_id)
        if len(book_copies) > 0:
            latest_copy = book_copies.latest("date_added")
            view_count = latest_copy.view_count
            rec_count = latest_copy.do_recommend_count
            dn_rec_count = latest_copy.do_not_recommend_count
            Book.delete(latest_copy)
        else:
            pass
        new_book = Book(title=result["meta_values"][0],
                        author=result["meta_values"][1],
                        language=result["meta_values"][2],
                        translater=result["meta_values"][3],
                        full_text=result["full_text"],
                        chapter_titles=result["chapter_titles"],
                        chapter_divisions=result["chapter_divisions"],
                        section_indices=result["section_indices"],
                        project_gutenberg_id=pg_id,
                        verified_public_domain=result["is_public_domain"],
                        view_count=view_count,
                        do_recommend_count=rec_count,
                        do_not_recommend_count=dn_rec_count)
        new_book.save()
        if cover_path != "":
            with open(cover_path, 'rb') as f:
                image_file = File(f)
                new_book.book_cover.save(str(result["pg_id"]) + "cover.png", image_file, save=True)
        new_book.save()
        add_subject_tags(new_book, result["meta_tags"])
    html_file.close()
    if cover_path != "":
        os.remove(cover_path)
    os.remove(html_path)
    if html_path != book_file_path:
        os.remove(book_file_path)


def handle_create_book_from_path(book_file_path):
    create_book_from_path(book_file_path)


def add_subject_tags(book, subject_tags: list):
    for tag in subject_tags:
        tag_model, tag_created = SubjectTag.objects.get_or_create(content=tag)
        tag_model.books.add(book)
        tag_model.num_books = len(tag_model.books.all())
        tag_model.save()
        if tag_created:
            try:
                print("NEW Tag: " + str(tag_model.content))
            except UnicodeEncodeError as e:
                print("Failed to print")



# Delete/invalidate cache contents if their source is altered
# @receiver(post_save, sender=Book)
@receiver(post_delete, sender=Book)
def clear_cache(sender, **kwargs):
    cache.delete('book_models')
    cache.delete('top_book_models')
    cache.delete('home_page_books')


@receiver(post_save, sender=SubjectTag)
@receiver(post_delete, sender=SubjectTag)
def clear_cache(sender, **kwargs):
    cache.delete('book_models')
    cache.delete('top_book_models')
    cache.delete('subject_tag_data')
    cache.delete('top_subject_tag_data')
    cache.delete('home_page_books')
