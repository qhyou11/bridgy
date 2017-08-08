import setuptools
import glob
import os

exec(open('./bridgy/version.py').read())

setuptools.setup(
    name='bridgy',
    version=__version__,
    url='https://github.com/wagoodman/bridgy',
    license=__license__,
    author=__author__,
    author_email=__email__,
    description='Easily search your cloud inventory and use ssh + tmux + sshfs',
    packages=setuptools.find_packages('bridgy'),
    package_dir={'': 'bridgy'},
    py_modules=[os.path.splitext(os.path.basename(path))[0] for path in glob.glob('bridgy/*.py')],
    include_package_data=True,
    install_requires=['PyYAML',
                      'requests',
                      'docopt',
                      'inquirer',
                      'fuzzywuzzy',
                      'boto3',
                      'placebo',
                      'coloredlogs',
                      'tabulate'],
    platforms='linux',
    keywords=['tmux', 'ssh', 'sshfs', 'aws', 'newrelic', 'inventory', 'cloud'],
    # latest from https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: System Shells',
        'Topic :: Terminals',
        'Topic :: Utilities',
        ],
    entry_points={
        'console_scripts': [
            'bridgy = bridgy:main'
        ]
    },
)
