from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(
    name='testrail-reporter',
    version='1.1.1',
    packages=find_packages(),
    package_data={'': ['etc/*', 'etc/maps/pytest/*', 'etc/maps/tempest/*']},
    install_requires=[
        'flake8',
        'pyyaml',
        'tox',
        'wheel',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'testrail-reporter = testrail_reporter.cmd.reporter:main'
        ]
    },
    # metadata to display on PyPI
    author='Ilya Bumarskov',
    author_email='bumarskov@gmail.com',
    description='Report test results to TestRail',
    long_description=long_description,
    url="https://github.com/ibumarskov/testrail-reporter",
)
