# pylint: disable=unused-argument
# pylint: disable=keyword-arg-before-vararg
# pylint: disable=inconsistent-return-statements
# pylint: disable=line-too-long
"""Custom authentication pipeline steps."""

from django.shortcuts import redirect
from social_core.pipeline.partial import partial


def auth_allowed(backend, details, response, *args, **kwargs):
    """Route unallowed auth attempts to error page."""
    if not backend.auth_allowed(response, details):
        return redirect('/login/error', error=True)
    return None


@partial
def collect_extra_info(
        strategy,
        backend,
        request,
        details,
        user=None,
        *args,
        **kwargs):
    """Collect extra information on sign up."""
    if user:
        return {'is_new': False}
    # session 'grad_year' is set by the pipeline infrastructure
    # because it exists in FIELDS_STORED_IN_SESSION
    grad_year = strategy.session_get('grad_year', None)
    if not grad_year:
        # if we return something besides a dict or None, then that is
        # returned to the user -- in this case we will redirect to a
        # view that can be used to get a password
        return redirect("/login/collect_extra_info")


USER_FIELDS = ['email', 'username']


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    Add extra information to saved user.

    Based on https://github.com/python-social-auth/social-core/blob/3.3.3/social_core/pipeline/user.py#L64
    """
    # User has registered previously.
    if user:
        return {'is_new': False}

    fields = dict((name, kwargs.get(name, details.get(name)))
                  for name in backend.setting('USER_FIELDS', USER_FIELDS))
    if not fields:
        return None

    # Add graduation year and computing ID. This is extra info not
    # automatically collected by python-social-auth.
    fields['graduation_year'] = strategy.session_get('grad_year', None)
    fields['computing_id'] = kwargs.get(
        'email', details.get('email')).split('@')[0]

    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }
