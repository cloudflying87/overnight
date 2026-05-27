"""
Template context processors for the care_tracking app.
"""
from .utils import get_shared_owners, resolve_subject


def sharing(request):
    """
    Expose read-only sharing state to every template:

      - ``shared_owners``: users who have shared their records with the
        current user (used to render the "viewing as" switcher).
      - ``current_subject``: the user whose records are currently shown.
      - ``viewing_is_owner``: True when viewing your own records (controls
        whether edit/create/delete actions are shown).
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {}

    subject, is_owner = resolve_subject(request)
    return {
        'shared_owners': get_shared_owners(request.user),
        'current_subject': subject,
        'viewing_is_owner': is_owner,
    }
