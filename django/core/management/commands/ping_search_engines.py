import logging
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.sitemaps import ping_search_engines


class Command(BaseCommand):
    help = "Ping all supported search engines with an updated sitemap and optionally, the url of the sitemap."

    def execute(self, *args, **options):
        logging.root.addHandler(logging.StreamHandler(sys.stderr))
        logging.root.setLevel(settings.DEBUG and logging.DEBUG or logging.INFO)
        if len(args) == 1:
            sitemap_url = args[0]
        else:
            sitemap_url = None
        ping_search_engines(sitemap_url=sitemap_url)

