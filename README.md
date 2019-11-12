# TestRail reporter
[![BuildStatus](https://travis-ci.com/ibumarskov/testrail-reporter.svg?branch=master)](https://travis-ci.com/ibumarskov/testrail-reporter)

The testrail-reporter repository contains scripts that allow to report test results to TestRail and analyze them.

**Features**
- Templates-based (yaml) mapping for pushing xml attributes to desired TestRail fields. Allows you to publish custom xml files.
- Bulk test publishing.
- Supports configurations for test plan entry (Test Run)
- Comparison and publishing failed SetUp classes (Currently tempest only)
- Publishing of Test Suites with template-based mappings for case attributes. PyTest and Tempest test lists are supported from the box.
- Analyzer of reported results.

## Know issues:
- Action for failed tearDownClass is't defined</li>

## Usage
Before use the script setup TestRail parameters: 

    export TESTRAIL_URL=<url>
    export TESTRAIL_USER=<user>
    export TESTRAIL_PASSWORD=<password>

### Publish results

    usage: reporter.py upload [-h] [-p TR_PROJECT] [-t TR_PLAN] [-r TR_RUN]
                              [-s TR_SUITE] [-m TR_MILESTONE] [-c TR_CONF]
                              [--update-suite] [--remove-untested]
                              [--case-attrs TR_CASE_ATTRS]
                              [--result-attrs TR_RESULT_ATTRS]
                              [--case-map TR_CASE_MAP]
                              [--result-map TR_RESULT_MAP]
                              [--sections-map SECTIONS_MAP]
                              Tempest report
    
    positional arguments:
      Tempest report        Path to tempest report (.xml)
    
    optional arguments:
      -h, --help            show this help message and exit
      -p TR_PROJECT         TestRail Project name.
      -t TR_PLAN            TestRail Plan name
      -r TR_RUN             TestRail Run name.
      -s TR_SUITE           TestRail Suite name.
      -m TR_MILESTONE       TestRail milestone.
      -c TR_CONF            Set configuration for test entry (Test Run). Example:
                            -c {'Contrail':'OC 4.1'}
      --update-suite        Update Test Suite
      --remove-untested     Remove untested cases from Test Run
      --case-attrs TR_CASE_ATTRS
                            Custom case attributes
      --result-attrs TR_RESULT_ATTRS
                            Custom result attributes
      --case-map TR_CASE_MAP
                            Custom case map
      --result-map TR_RESULT_MAP
                            Custom result map
      --sections-map SECTIONS_MAP
                            Custom section map

### Update test suite

**Template for test case list**

You can provide custom template to map title and suite name for test. For title and suite are supported following actions (in order of priority):

- custom-map - contains list of dictionaries. Checks if test case match dict.value (re.search() is used) and return dict.key as name.
- find - get first element found by re.findall() function.
- replace - replaces all occurrences of found substrings.

Example of template: *etc/maps/pytest/testlist.yaml*

### Analyze results

    usage: reporter.py analyze [-h] [-p TR_PROJECT] [-t TR_PLAN] [-r TR_RUN]
                               Check list
    
    positional arguments:
      Check list     Path to check list (.yml)
    
    optional arguments:
      -h, --help     show this help message and exit
      -p TR_PROJECT  TestRail Project name.
      -t TR_PLAN     TestRail Plan name
      -r TR_RUN      TestRail Run name.

## Run script from docker image
To run testrail_reporter against TestRail using docker image:
1. Pull docker image from [dockerhub](https://hub.docker.com/r/bumarskov/testrail_reporter)
`docker push bumarskov/testrail_reporter:<tagname>`
2. Run qa_report.py script to upload test results:
`docker run -v '<path_to_results>:/tmp/result.xml' -e $TESTRAIL_URL="<url>" -e $TESTRAIL_USER="<user>" -e $TESTRAIL_PASSWORD="<password>" testrail_reporter:<tagname> python reporter.py upload /tmp/<results_file> -p "<TestRail project>" -t "<TestRail test plan>" -r "<TestRail test run>" -s "<TestRail suite>" -c`

## How to build docker image
Before build docker image from local copy of repository remove all `.*pyc` files and `__pycache__` folder:

`find lib/ -name "*.pyc" -exec rm -f {} \;
rm -rf lib/__pycache__`

Build image:
`docker build --tag=alpha .`
