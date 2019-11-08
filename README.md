# TestRail reporter
[![BuildStatus](https://travis-ci.com/ibumarskov/testrail-reporter.svg?branch=master)](https://travis-ci.com/ibumarskov/testrail-reporter)
<p>The testrail-reporter repository contains scripts that allow to report test results to TestRail and analyze them.</p>

**Features**
<ul>
<li>Templates-based (yaml) mapping for pushing xml attributes to desired TestRail fields. Allows you to publish custom xml files.</li>
<li>Bulk and per test publishing (WIP).</li>
<li>Supports configurations for test plan entry (Test Run)</li>
<li>Comparison and publishing failed SetUp classes (Currently tempest only)</li>
<li>Publishing of Test Suites (WIP)</li>
<li>Analyzer of reported results.</li>
</ul>

## Know issues:
<ul>
<li>Action for failed tearDownClass is't defined</li>
<li>Publishing of test cases without section isn't supported yet (WIP)</li>
</ul>

## Usage
Before use the script setup TestRail parameters: 

    export TESTRAIL_URL=<url>
    export TESTRAIL_USER=<user>
    export TESTRAIL_PASSWORD=<password>

**Upload results**

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

**Analyze results**

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
