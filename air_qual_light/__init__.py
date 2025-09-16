import os

# Allow developments on a non-raspberry pi hardware.
RASPBERRY_PI_HARDWARE = str(os.getenv('RASPBERRY_PI_HARDWARE', 'TRUE'))
if RASPBERRY_PI_HARDWARE is not True:
    if RASPBERRY_PI_HARDWARE.upper() in {'TRUE', 'YES', '1'}:
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
    except ImportError:
        raise ValueError('Cannot find version number from scm or pkg resources')
    except DistributionNotFound:  # type: ignore
        raise ValueError('Cannot find version number from scm or pkg resources')

base_version = '.'.join(version.split('.')[:3])
