
from django.core.management.base import BaseCommand
from GutenReaderApp.tasks import retry_chapter_titles


class Command(BaseCommand):
    help = 'run retry_chapter_titles function'

    def handle(self, *args, **kwargs):
        try:
            retry_chapter_titles()
        except Exception as e:
            print("Exception while running retry_chapter_titles function: " + str(e))
