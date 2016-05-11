"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='robob',
    version='0.2.1',

    description='A python tool for simplifying collection of measurements over repetitive tasks',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/wavesoft/robob',

    # Author details
    author='Ioannis Charalampidis',
    author_email='johnys2@gmail.com',

    # License
    license='Apache-2.0',

    # Classifiers
    classifiers=[

        # Project maturity
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',

        # Topics
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',

        # License
        'License :: OSI Approved :: Apache Software License',

        # Python versions (tested)
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    # What does your project relate to?
    keywords='automation benchmark scripting test',

    # Packages
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Project dependencies
    install_requires=['PyYAML'],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'robob=robob.cli:main',
        ],
    },
)
