import setuptools


with open('README.md') as fp:
    long_description = fp.read()

setup_requires = [
    'setuptools_scm',
]

requirements = [
    'aiohttp',
    'Click',
    'numpy',
    'rpi_ws281x',
    'adafruit-circuitpython-neopixel'
]

test_requirements = [
    'pytest',
]

setuptools.setup(
    name='air_qual_light',
    setup_requires=setup_requires,
    use_scm_version=True,
    description='Updates led light after a PurpleAir monitor value',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Magnus Isaksson',
    packages=['air_qual_light'],
    package_data={'air_qual_light': ['config/*']},
    include_package_data=True,
    install_requires=requirements,
    python_requires='>=3.7',
    zip_safe=False,
    keywords='air_qual_light',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering'
    ],
    test_suite='tests',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': [
            'airqual = air_qual_light.cli:main'
        ]
    }
)
