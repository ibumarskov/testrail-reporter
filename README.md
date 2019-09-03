# QA-reports
The QA-reports repository contains scripts that allow to report test results to TestRail and analyze them.
Supports templates (yaml based) for pushing xml attributes to desired TestRail fields.

## Know issues:
#. upload_test_suite.py doesn't parse rst file with one test (due to specifics of the docutils library)

### Run script from docker image
To run qa_reports against TestRail using docker image:
1. Pull docker image from [dockerhub](https://hub.docker.com/r/bumarskov/qa_reports)
`docker push bumarskov/qa_reports:<tagname>`
2. Run qa_report.py script to upload test results:
`docker run -v '<path_to_results>:/tmp/result.xml' -e $TESTRAIL_URL="<url>" -e $TESTRAIL_USER="<user>" -e $TESTRAIL_PASSWORD="<password>" qa_reports:<tagname> python qa_reports.py upload /tmp/<results_file> -p "<TestRail project>" -t "<TestRail test plan>" -r "<TestRail test run>" -s "<TestRail suite>" -c`

## How to build docker image
Before build docker image from local copy of repository remove all `.*pyc` files and `__pycache__` folder:

`find lib/ -name "*.pyc" -exec rm -f {} \;
rm -rf lib/__pycache__`

Build image:
`docker build --tag=alpha .`
