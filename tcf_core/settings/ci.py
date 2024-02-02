# pylint: disable=unused-wildcard-import,wildcard-import,fixme
"""
Django settings module for CI services such as Travis or GitHub Actions

Unlike other files where we use environment variables for everything, it is
okay to use some strings constants here and in .travis.yml or python-app.yml
"""
from .base import *

# The following if statement is needed to prevent overwriting global variables when
# this settings file is interpreted
if os.environ.get("DJANGO_SETTINGS_MODULE") == "tcf_core.settings.ci":
    pass
