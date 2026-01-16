# pylint: disable=missing-module-docstring
"""
Settings package for tcf_core.

Environment settings are loaded via DJANGO_SETTINGS_MODULE:
  - Local dev:  tcf_core.settings.dev  (manage.py default)
  - CI:         tcf_core.settings.ci   (set in ci.yml)
  - Production: tcf_core.settings.prod (wsgi.py default)

This file intentionally does NOT import any settings to prevent
import side effects that can cause unexpected behavior across environments.
"""
