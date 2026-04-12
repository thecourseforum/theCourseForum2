"""
Settings package for tcf_core.

Environment settings are loaded via DJANGO_SETTINGS_MODULE:
  - Local dev + CI: tcf_core.settings.dev  (manage.py default; CI sets same via workflow env)
  - Production:     tcf_core.settings.prod (wsgi.py default)

This file intentionally does NOT import any settings to prevent
import side effects that can cause unexpected behavior across environments.
"""
