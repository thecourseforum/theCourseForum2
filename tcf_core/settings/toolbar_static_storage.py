"""Static storage that serves debug toolbar assets from the dev server."""

from django.conf import settings
from storages.backends.s3 import S3ManifestStaticStorage

TOOLBAR_PREFIX = "debug_toolbar/"


class ToolbarS3ManifestStaticStorage(S3ManifestStaticStorage):
    """Keep toolbar assets off the CDN path used for the rest of the site.

    django-debug-toolbar is a dev-only dependency, so the prod-image release
    task that runs collectstatic never uploads its assets to the static bucket.
    """

    def url(self, name, *args, **kwargs):
        if name.startswith(TOOLBAR_PREFIX):
            return f"{settings.STATIC_URL}{name}"
        return super().url(name, *args, **kwargs)
