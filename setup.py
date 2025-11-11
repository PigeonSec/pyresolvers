"""PyResolvers setup configuration"""
from setuptools import find_packages, setup
import os


def dependencies(imported_file):
    """Load dependencies from requirements file"""
    with open(imported_file, encoding='utf-8') as file:
        return file.read().splitlines()


def get_version():
    """Get version from __version__.py file"""
    version_file = os.path.join('pyresolvers', 'lib', 'core', '__version__.py')
    with open(version_file, encoding='utf-8') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return '1.0.0'


with open("README.md", encoding='utf-8') as file:
    long_description = file.read()

setup(
    name="pyresolvers",
    license="GPLv3",
    description="High-performance async DNS resolver validation and speed testing library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Karl",
    version=get_version(),
    author_email="",
    url="https://github.com/PigeonSec/pyresolvers",
    project_urls={
        "Bug Tracker": "https://github.com/PigeonSec/pyresolvers/issues",
        "Documentation": "https://github.com/PigeonSec/pyresolvers#readme",
        "Source Code": "https://github.com/PigeonSec/pyresolvers",
    },
    keywords=['dns', 'resolver', 'validation', 'speed-test', 'async', 'networking'],
    packages=find_packages(exclude=('tests',)),
    package_data={'pyresolvers': ['*.txt']},
    entry_points={
        'console_scripts': [
            'pyresolvers = pyresolvers.__main__:main'
        ]
    },
    install_requires=dependencies('requirements.txt'),
    setup_requires=['pytest-runner'],
    tests_require=dependencies('test-requirements.txt'),
    include_package_data=True,
    python_requires='>=3.12',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Topic :: Internet :: Name Service (DNS)',
        'Topic :: System :: Networking',
    ],
)
