try:
    from .version import version as __version__
except ImportError:  # pragma: nocover
    __version__ = "master"
