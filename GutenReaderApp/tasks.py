import os
import requests
from django_q.tasks import async_task
from GutenReaderApp.models import handle_create_book_from_path

successful_paths = []
base_url = 'http://aleph.gutenberg.org/cache/epub/'


def attempt_write_to_file(path, file_name, url):
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
    # for path in successful_paths:
    #     try:
    #         handle_create_book_from_path(path)
    #     except Exception as e:
    #         print("Failed to Create Book, \nException: " + str(e))


def run_download_files_async_task(start, distance):
    async_task('GutenReaderApp.tasks.download_files', start, distance)
