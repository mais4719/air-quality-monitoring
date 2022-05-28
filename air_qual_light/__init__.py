import os

# Allow developmnet on a non-rasberry pi hardware.
RASPBERRY_PI_HARDWARE = os.getenv('RASPBERRY_PI_HARDWARE', True)
if RASPBERRY_PI_HARDWARE is not True:
    if RASPBERRY_PI_HARDWARE.upper() in ('TRUE', 'YES'):
        RASPBERRY_PI_HARDWARE = True
    else:
        RASPBERRY_PI_HARDWARE = False

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
