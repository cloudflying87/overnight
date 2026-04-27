"""
Custom storage backends for static files
"""

from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class NonStrictManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    Like ManifestStaticFilesStorage but doesn't raise errors on missing files.
    This is useful when some static files are referenced but might not be present,
    or when the manifest gets out of sync.
    """
    manifest_strict = False
