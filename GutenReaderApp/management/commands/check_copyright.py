
from django.core.management.base import BaseCommand
from GutenReaderApp.tasks import check_copyright


class Command(BaseCommand):
    help = 'run check_copyright function'

    def handle(self, *args, **kwargs):
        try:
            check_copyright()
        except Exception as e:
            print("Exception while running check_copyright function: " + str(e))
