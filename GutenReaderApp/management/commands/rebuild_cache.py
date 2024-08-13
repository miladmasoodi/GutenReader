
from django.core.management.base import BaseCommand
from GutenReaderApp.tasks import rebuild_cache


class Command(BaseCommand):
    help = 'run rebuild_cache function'

    def handle(self, *args, **kwargs):
        try:
            rebuild_cache()
        except Exception as e:
            print("Exception while running rebuild_cache function: " + str(e))
