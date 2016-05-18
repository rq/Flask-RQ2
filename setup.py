import codecs
import os
import sys

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
# Get the long description from the README file
with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


tests_require = [
    'pytest',
    'redis',
    'rq-scheduler',
    'flask-cli>=0.3.0',
    'flask-script',
    'coverage>=4.0',
    'pytest-isort',
    'pytest-cache>=1.0',
    'pytest-flake8>=0.5',
    'pytest>=2.8.0',
    'pytest-wholenodeid',
    'pytest-capturelog',
]

extras_require = {
    'docs': [
        'Sphinx>=1.4',
    ],
    'cli': [
        'Flask-CLI>=0.3.0',
    ],
    'script': [
        'Flask-Script',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

needs_pytest = set(['pytest', 'test', 'ptr']).intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

setup_params = dict(
    name='Flask-RQ2',
    version='16.0',
    url='https://flask-rq2.readthedocs.io/',
    license='MIT',
    author='Jannis Leidel',
    author_email='jannis@leidel.info',
    description='Very short description',
    long_description=long_description,
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    setup_requires=[] + pytest_runner,
    install_requires=[
        'Flask>=0.10',
        'rq>=0.6.0',
        'rq-scheduler>=0.6.1',
    ],
    extras_require=extras_require,
    tests_require=tests_require,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators ',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Unix ',
        'Programming Language :: Python',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
    ]
)

if __name__ == '__main__':
    setup(**setup_params)
