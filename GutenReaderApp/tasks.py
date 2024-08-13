import os
import time

import requests
from django_q.tasks import async_task
from django.core.cache import cache
from django.core.management import call_command
from GutenReaderApp.models import handle_create_book_from_path, Book, SubjectTag
from GutenReaderApp.views import get_tags_order_by, get_books_order_by, get_home_books, NUM_TOP_BOOKS_HOME

successful_paths = []
base_url = 'http://aleph.gutenberg.org/cache/epub/'


def attempt_write_to_file(path, file_name, url):
    """Downloads the content from a given URL and writes it to a file.
    Returns boolean: True if the file was successfully downloaded, False otherwise."""
    response = requests.get(url)
    if response.status_code == 200:
        complete_path = os.path.join(path, file_name)
        with open(complete_path, 'wb') as file:
            file.write(response.content)
        successful_paths.append(complete_path)
        print(f'Successfully downloaded: {url}')
        return True
    else:
        print(f'Failed to download: {url} (Status code: {response.status_code})')
        return False


def download_files(start, distance):
    """Downloads files (from base_url) numbered <start> until <start+distance>, then call rebuild_cache to recache
    and rebuild_index to rebuild search index"""
    file_folder = "Book_Files"
    path = file_folder
    if not os.path.exists(path):
        os.makedirs(path)
    for pg_id in range(start, start + distance + 1):
        url = base_url
        pg_id_string = str(pg_id)
        print(pg_id_string)
        final_url = url + f'{pg_id_string}/pg{pg_id_string}-h.zip'
        file_name = 'PG' + pg_id_string
        result = attempt_write_to_file(path, file_name + ".zip", final_url)
        if not result:
            print('Attempting download of html file instead of zip')
            alt_url = url + f'{pg_id_string}/pg{pg_id_string}-images.html'
            attempt_write_to_file(path, file_name + ".html", alt_url)
        else:  # on success from attempt_write_to_file()
            try:
                handle_create_book_from_path(successful_paths[-1])
            except Exception as e:
                print("Failed to Create Book, \nException: " + str(e))
    print('\n@@@@@@@@@@@@@@@@@@@@@@@ Finished Downloads @@@@@@@@@@@@@@@@@@@@@@@\n')
    rebuild_cache()
    print('rebuilding search index')
    rebuild_search_index()


def rebuild_cache():  # deletes existing caches then calls methods that will generate them
    print("Deleting Existing Caches")
    cache.delete('book_models')
    cache.delete('top_book_models')
    cache.delete('subject_tag_data')
    cache.delete('top_subject_tag_data')
    cache.delete('home_page_books')
    print("Starting Caching:")
    # start caching
    start_time = time.time()
    get_books_order_by()
    get_tags_order_by()
    get_home_books()
    end_time = time.time()
    time_taken = end_time - start_time
    print('\n@@@@@@@@@@@@@@@@@@@@@@@ Finished Caching @@@@@@@@@@@@@@@@@@@@@@@\n')
    print(f'Total time: {time_taken:.3f} seconds')


def check_copyright():  # finds any non public-domain books, then prompts to delete them
    books_to_delete = []
    all_books = Book.objects.all()
    print("Starting Copyright check")
    for book in all_books:
        if book.verified_public_domain is False:
            books_to_delete.append(book)
    if len(books_to_delete) == 0:
        print("ALL CLEAR for Copyright check")
        return
    print(books_to_delete)
    print("Delete? (y to continue)")
    choice = input()
    if choice[0] == "y":
        for book in books_to_delete:
            Book.delete(book)
        print("Deletion completed")
    else:
        print("Process cancelled")


def count_tag_num_books():  # assigns t.num_books for all tags, for development only
    all_tags = SubjectTag.objects.all()
    print("Starting tag num_books count")
    for tag in all_tags:
        tag.num_books = len(tag.books.all())
        tag.save()
    print("Finished tag num_books count")


def rebuild_search_index():  # calls whoosh/haystack command to rebuild search index
    call_command('rebuild_index', interactive=False)


def run_download_files_async_task(start, distance):
    async_task('GutenReaderApp.tasks.download_files', start, distance)
