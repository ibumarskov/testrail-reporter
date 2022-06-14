# TestRail reporter
[![CircleCI](https://circleci.com/gh/ibumarskov/testrail-reporter/tree/master.svg?style=svg)](https://circleci.com/gh/ibumarskov/testrail-reporter/?branch=master)

The testrail-reporter repository contains scripts that allow to report test results to TestRail and analyze them.

**Features**
- Templates-based (yaml) mapping for pushing xml attributes to desired TestRail fields. Allows you to publish custom xml files.
- Bulk test publishing.
- Supports configurations for test plan entry (Test Run)
- Comparison and publishing failed SetUp classes (Currently tempest only)
- Publishing of Test Suites with template-based mappings for case attributes. PyTest and Tempest test lists are supported from the box.
- Analyzer of reported results.

## Know issues and limitations:
- Nested sections aren't supported

## Installation

    python3 setup.py install

## Usage
Set the TestRail parameters before using the script:

    export TESTRAIL_URL=<url>
    export TESTRAIL_USER=<user>
    export TESTRAIL_PASSWORD=<password>

### Publish results

    usage: testrail-reporter publish [-h] [-p TR_PROJECT] [-t TR_PLAN] [-r TR_RUN] [-s TR_SUITE] [-m TR_MILESTONE] [-c TR_CONF] [--plan-description TR_PLAN_DESCR] [--run-description TR_RUN_DESCR] [--limit LIMIT]
                                 [--remove-untested] [--remove-skipped] [--result-attrs TR_RESULT_ATTRS] [--map MAP]
                                 Tempest report

    positional arguments:
      Tempest report        Path to tempest report (.xml)
    
    options:
      -h, --help            show this help message and exit
      -p TR_PROJECT         TestRail Project name.
      -t TR_PLAN            TestRail Plan name
      -r TR_RUN             TestRail Run name.
      -s TR_SUITE           TestRail Suite name.
      -m TR_MILESTONE       TestRail milestone.
      -c TR_CONF            Set configuration for test entry (Test Run). Example: -c "{'Operating Systems':'Ubuntu 18.04'}"
      --plan-description TR_PLAN_DESCR
                            Test Plan description.
      --run-description TR_RUN_DESCR
                            Test Run description.
      --limit LIMIT         Limit the length of the comments in bytes
      --remove-untested     Remove untested cases from Test Run
      --remove-skipped      Remove skipped cases from Test Run
      --result-attrs TR_RESULT_ATTRS
                            Set path to config file with custom result attributes (.yaml format).
      --map MAP             Use predefined map for parsing attributes. Supported values:tempest, pytest

### Update test suite

    usage: testrail-reporter update [-h] [-p TR_PROJECT] [-s TR_SUITE] [--case-attrs TR_CASE_ATTRS] [--map MAP] [--tc-map TR_CASE_MAP] List of test cases

    positional arguments:
      List of test cases    Path to file with list of tests.
    
    options:
      -h, --help            show this help message and exit
      -p TR_PROJECT         TestRail Project name.
      -s TR_SUITE           TestRail Suite name.
      --case-attrs TR_CASE_ATTRS
                            Set path to config file with custom case attributes (.yaml format).
      --map MAP             Use predefined map for parsing case attributes. Supported values: tempest, pytest
      --tc-map TR_CASE_MAP  Set path to config file with custom case map. Note: this parameter overrides predefined map parameter.


### Analyze results

    usage: testrail-reporter analyze [-h] [-p TR_PROJECT] [-t TR_PLAN] [-r TR_RUN] [-c TR_CONF] Check list

    positional arguments:
      Check list     Path to check list (.yml)
    
    options:
      -h, --help     show this help message and exit
      -p TR_PROJECT  TestRail Project name.
      -t TR_PLAN     TestRail Plan name
      -r TR_RUN      TestRail Run name.
      -c TR_CONF     Set configuration for test entry (Test Run). Example: -c "{'Operating Systems':'Ubuntu 18.04'}"

## Templates and actions

### Template for results

**Attributes description:**

- *tc_tag* - name of xml element's tag that contains test case result. XML elements with another tags (exclude child elements) will be ignored.
- *test_id* - section describes action for generation of test title.
- *status_id* - section describes action for generation of test status.
- *comments* - section describes action for generation of comments (logs).

Each section can contains following attributes:
- *default* - default value for attribute if action returns empty string (not applicable for test_id section)
- *xml_actions* - actions that will be applied for xml element. Description of supported XML actions can be found [below](#xml-actions). 

**Results for setUp/tearDown classes:**

Optionally template can contains filter and actions for setUp and tearDown classes:
- *filter_setup* (optionally) - contains filters and actions for setUp results.
- *filter_teardown* (optionally) - contains filters and actions for tearDown results.

if sections are determined, they must contains following attributes:
- *match* - regular expression pattern. Only if test name matches the pattern, another actions will be executed.
- *status_id* (optionally) - replace original test status with custom status. Replace status only if original status is "passed". Otherwise, leave the original status.
- *actions* - list of action for string generation. Description of supported actions can be found [below](#actions).

Example of template: *testrail_reporter/etc/maps/pytest/result_template.yaml*

### Template for test cases 

**Attributes description:**

Many frameworks provide the ability to print list of test cases. Examples:
 
    pytest --collect-only -q .
    tempest run -l
 
 Using test case template you can generate list with test cases to update TestRail's Test Suite.
 - *title* - contains list of actions for generation test name. 
 - *section* - contains list of actions for generation test name. Description of supported actions can be found [below](#actions).

### Template for custom case fields

This template is used for convert name of custom attribute to id.

- *attributes2id* - contains list with name of custom case attributes required to be converted to id.

Example of template: *testrail_reporter/etc/attrs2id.yaml*

### Actions for string generation {#actions}

- *custom-map* - contains list of dictionaries. Checks if test case match dict.value (re.search() is used) and return dict.key as name.
- *find* - get first element found by re.findall() function.
- *replace* - replaces all occurrences of found substrings.

### Actions for string generation from xml file {#xml-actions}

XML actions are used to generate string from XML file. All actions are performed in the order specified in template.

- *add_string* - add (concatenate) custom string.
- *get_attribute* - add (concatenate) xml attribute value with the specified name.
- *get_element_text* - add (concatenate) element's text.
- *has_child_tag* - check if element contains child with specified tag and 
  execute xml_actions (must be specified) for this element.

## Docker image

### Run script from docker image
To run testrail_reporter against TestRail using docker image:
1. Pull docker image from [dockerhub](https://hub.docker.com/r/bumarskov/testrail_reporter)
`docker push bumarskov/testrail_reporter:<tagname>`
2. Run qa_report.py script to upload test results:
`docker run -v '<path_to_results>:/tmp/report.xml' -e TESTRAIL_URL="<url>" -e TESTRAIL_USER="<user>" -e TESTRAIL_PASSWORD="<password>" testrail-reporter:<tagname> python reporter.py publish /tmp/report.xml -p "<TestRail project>" -t "<TestRail test plan>" -r "<TestRail test run>" -s "<TestRail suite>" -c "<Configuration>" --remove-untested`

### How to build docker image
Before build docker image from local copy of repository remove all `.*pyc` files and `__pycache__` folder.

Build image:
`docker build --tag=testrail-reporter:alpha .`
