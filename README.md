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

## Know issues and limitations:
- Nested sections aren't supported

## Usage
Before use the script set TestRail parameters: 

    export TESTRAIL_URL=<url>
    export TESTRAIL_USER=<user>
    export TESTRAIL_PASSWORD=<password>

### Publish results

    usage: reporter.py publish [-h] [-p TR_PROJECT] [-t TR_PLAN] [-r TR_RUN]
                               [-s TR_SUITE] [-m TR_MILESTONE] [-c TR_CONF]
                               [--remove-untested]
                               [--result-attrs TR_RESULT_ATTRS]
                               [--result-map TR_RESULT_MAP]
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
                            -c "{'Contrail':'OC 4.1'}"
      --remove-untested     Remove untested cases from Test Run
      --result-attrs TR_RESULT_ATTRS
                            Custom result attributes
      --result-map TR_RESULT_MAP
                            Custom result map

### Update test suite

    usage: reporter.py update [-h] [-p TR_PROJECT] [-s TR_SUITE]
                              [--tc-map TESTCASE_MAP]
                              List of test cases
    
    positional arguments:
      List of test cases    Path to file with list of tests.
    
    optional arguments:
      -h, --help            show this help message and exit
      -p TR_PROJECT         TestRail Project name.
      -s TR_SUITE           TestRail Suite name.
      --tc-map TESTCASE_MAP
                            TestCase map

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

## Templates and actions

### Template for results

**Attributes description:**

- *tc_tag* - name of xml element's tag that contains test case result. XML elements with another tags (exclude child elements) will be ignored.
- *test_id* - section describes action for generation of test title .
- *status_id* - section describes action for generation of test status.
- *comments* - section describes action for generation of comments (logs).

Each section can contains following attributes:
- *default* - default value for attribute if action returns empty string (not applicable for test_id section)
- *xml_actions* - actions that will be applied for xml element. Description of supported XML actions can be found below. 

**Results for setUp/tearDown classes:**

Optionally template can contains filter and actions for setUp and tearDown classes:
- *filter_setup* (optionally) - contains filters and actions for setUp results.
- *filter_teardown* (optionally) - contains filters and actions for tearDown results.

if sections are determined, they must contains following attributes:
- *match* - regular expression pattern. Only if test name matches the pattern, another actions will be executed.
- *status_id* (optionally) - set custom status
- *actions* - list of action for string generation. Description of supported actions can be found below.

Example of template: *etc/maps/pytest/case_template.yaml*

### Template for test cases

**Attributes description:**

Many frameworks provide the ability to print list of test cases. Examples:
 
    pytest --collect-only -q .
    tempest run -l
 
 Using test case template you can generate list with test cases to update TestRail's Test Suite. Template supports generation of *title* and *section* for each test in tests list. For title and section are supported actions that can be found here: <>

### Template for custom case fields

This template is used for convert name of custom attribute to id.

- *attributes2id* - contains list with name of custom case attributes required to be converted to id.

Example of template: *etc/attrs2id.yaml*

### Actions for string generation (actions)

- *custom-map* - contains list of dictionaries. Checks if test case match dict.value (re.search() is used) and return dict.key as name.
- *find* - get first element found by re.findall() function.
- *replace* - replaces all occurrences of found substrings.

### Actions for string generation from xml file (xml_actions)

XML actions are used to generate string from XML file. All actions are performed in the order specified in template.

- *get_attribute* - add (concatenate xml attribute value with the specified name.
- *add_string* - add (concatenate) custom string.
- *get_element_text* - add
- *check* - checks specified condition and execute xml_actions if True. This action allow to take nested xml elements.
    - *parent* - checks for specified attribute for current xml element:
        - *attribute* - сheck for the specified xml attribute.
        - *xml_actions* - execute xml_action for current element.
    - *child* - checks of availability of child xml element with specified tag and/or attribute:
        - *tag* - сheck for the specified tag in child element.
        - *attribute* - сheck for the specified xml attribute.
        - *xml_actions* - execute xml_action for child element.

## Docker image

### Run script from docker image
To run testrail_reporter against TestRail using docker image:
1. Pull docker image from [dockerhub](https://hub.docker.com/r/bumarskov/testrail_reporter)
`docker push bumarskov/testrail_reporter:<tagname>`
2. Run qa_report.py script to upload test results:
`docker run -v '<path_to_results>:/tmp/result.xml' -e $TESTRAIL_URL="<url>" -e $TESTRAIL_USER="<user>" -e $TESTRAIL_PASSWORD="<password>" testrail_reporter:<tagname> python reporter.py publish /tmp/<results_file> -p "<TestRail project>" -t "<TestRail test plan>" -r "<TestRail test run>" -s "<TestRail suite>" -c`

### How to build docker image
Before build docker image from local copy of repository remove all `.*pyc` files and `__pycache__` folder:

`find lib/ -name "*.pyc" -exec rm -f {} \;
rm -rf lib/__pycache__`

Build image:
`docker build --tag=alpha .`
