"""TCF Django Web Application."""

from django.apps import AppConfig


class TcfWebsiteConfig(AppConfig):
    """TCF Django Web Application Configuration."""

    name = "tcf_website"

    def ready(self):
        """Register signal handlers (e.g. denormalized review-stat upkeep, #982)."""
        # Imported for the import side effect of connecting the receivers.
        from . import signals  # noqa: F401
