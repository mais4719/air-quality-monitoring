try:
    from setuptools_scm import get_version
    __version__ = version = get_version(root='..', relative_to=__file__)
except (ImportError, LookupError):
    try:
        from pkg_resources import get_distribution, DistributionNotFound
        __version__ = version = get_distribution(__name__).version
    except (ImportError, DistributionNotFound):
        raise ValueError('Cannot find version number from scm or pkg resources')

base_version = '.'.join(version.split('.')[:3])
