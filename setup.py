from setuptools import find_packages, setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='testrail-reporter-tool',
    version='1.4.0',
    packages=find_packages(),
    package_data={'': ['etc/*', 'etc/maps/locust/*', 'etc/maps/pytest/*',
                       'etc/maps/tempest/*']},
    python_requires='>=3.6',
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
    description='TestRail reporter tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/ibumarskov/testrail-reporter",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Topic :: Software Development :: Quality Assurance',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='testrail reporter pytest tempest',
)
