
from django.core.management.base import BaseCommand
from GutenReaderApp.tasks import run_download_files_async_task


class Command(BaseCommand):
    help = 'run download_files task'

    def add_arguments(self, parser):
        parser.add_argument('start', type=int, help='starting PG file number')
        parser.add_argument('distance', type=int, help='How many files to download, starting from START')

    def handle(self, *args, **kwargs):
        try:
            start = kwargs['start']
            distance = kwargs['distance']
            run_download_files_async_task(start, distance)
        except Exception as e:
            print("Exception while running download_files command: " + str(e))
