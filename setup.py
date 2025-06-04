import codecs
import os

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
# Get the long description from the README file
with codecs.open(os.path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="Flask-RQ2",
    use_scm_version={"version_scheme": "post-release", "local_scheme": "dirty-tag"},
    url="https://flask-rq2.readthedocs.io/",
    license="MIT",
    author="Jannis Leidel",
    author_email="jannis@leidel.info",
    description="A Flask extension for RQ.",
    long_description=long_description,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    setup_requires=["setuptools_scm"],
    install_requires=[
        "Flask>=0.10",
        "rq>=2.3.3",
        "redis>=3.0.0",
        "rq-scheduler>=0.9.0",
    ],
    extras_require={
        "cli": ["Flask-CLI>=0.4.0"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators ",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Operating System :: Unix ",
        "Programming Language :: Python",
        "Topic :: Internet",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
)
