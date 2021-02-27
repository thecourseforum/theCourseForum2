# pylint: disable=import-outside-toplevel, unused-import
"""TCF Django Web Application."""

from django.apps import AppConfig


class TcfWebsiteConfig(AppConfig):
    """TCF Django Web Application Configuration."""
    name = 'tcf_website'

    # Source: https://stackoverflow.com/a/21612050
    def ready(self):
        import tcf_website.signals
