
from django.core.management.base import BaseCommand
from GutenReaderApp.tasks import count_tag_num_books


class Command(BaseCommand):
    help = 'run count_tag_num_books function'

    def handle(self, *args, **kwargs):
        try:
            count_tag_num_books()
        except Exception as e:
            print("Exception while running count_tag_num_books function: " + str(e))
