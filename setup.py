from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(
    name='testrail-reporter',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'flake8',
        'pyyaml',
        'tox',
        'wheel',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'testrail-reporter = reporter:main'
        ]
    },
    # metadata to display on PyPI
    author='Ilya Bumarskov',
    author_email='bumarskov@gmail.com',
    description='Report test results to TestRail',
    long_description=long_description,
    url="https://github.com/ibumarskov/testrail-reporter",
)
