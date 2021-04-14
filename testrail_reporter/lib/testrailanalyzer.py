import logging
import sys

import yaml
import re

from testrail_reporter.lib.exceptions import NotFound
from testrail_reporter.lib.testrailproject import TestRailProject

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler(sys.stdout))


class CheckListParser(object):
    def __init__(self, check_list_attrs='etc/check_list_example.yaml'):
        with open(check_list_attrs, 'r') as stream:
            self.attrs = yaml.safe_load(stream)
        self._check_structure()

    def _check_structure(self):
        for test in self.attrs['tests']:
            if 'title' not in test:
                raise NotFound("Title attribute")
            if 'status' not in test:
                raise NotFound("Status attribute")
            if 'errors' not in test:
                test['errors'] = None
            if 'defects' not in test:
                test['defects'] = None


class TestRailAnalyzer:

    def __init__(self, project, run_name, plan_name=None,
                 configuration=None):
        isinstance(project, TestRailProject)
        self.project = project
        conf_ids = []
        if configuration:
            isinstance(configuration, dict)
            conf_ids = self.project.get_config_ids(configuration)
            conf_ids.sort()
        self.test_run = None
        if plan_name:
            self.test_plan = self.project.get_plan_by_name(plan_name)
            for entry in self.test_plan['entries']:
                if run_name == entry['name']:
                    for run in entry['runs']:
                        run['config_ids'].sort()
                        if run['config_ids'] == conf_ids:
                            self.test_run = self.project.get_run(run['id'])
        else:
            self.test_run = self.project.get_run_by_name(run_name)
        if not self.test_run:
            raise NotFound("Can't find test run '{}' with configuration '{}'"
                           "".format(run_name, configuration))
        self.tests = self._get_failed_tests()

    def _get_failed_tests(self):
        status_id = self.project.get_status_by_label("failed")
        tests_filter = self.project.get_tests_filter(status_id=[status_id])
        return self.project.get_tests(self.test_run['id'], filter=tests_filter)

    def _check_errors(self, check_obj, test):
        test_res = self.project.get_results(test['id'])
        current_res = test_res[-1]
        if check_obj['errors']:
            for err in check_obj['errors']:
                if not current_res['comment']:
                    LOG.warning("Test result for {} doesn't contain any log."
                             "".format(test["title"]))
                    return False
                if err in current_res['comment']:
                    pass
                else:
                    LOG.info("Can't find string: {}".format(err))
                    LOG.warn("Test results for {} don't match know issue."
                             "".format(test["title"]))
                    return False
        msg = "Set by result analyzer"
        status = self.project.get_status_by_label(check_obj['status'])
        defects = check_obj['defects']
        data = self.project.result_data(status, comment=msg, defects=defects)
        self.project.add_result(test['id'], data)
        LOG.info("Test '{}' set to {}".format(test["title"],
                                              check_obj['status']))

    @staticmethod
    def _match_found(pattern, text):
        try:
            return re.search(pattern, text)
        except re.error as e:
            return pattern == text

    def analyze_results(self, check_list_obj):
        isinstance(check_list_obj, CheckListParser)
        check_objs_by_titles = {
            check_obj['title']: check_obj
            for check_obj in check_list_obj.attrs['tests']
            if not check_obj.get('title_type', '') == 'regexp'
        }

        tests_by_titles = {
            test['title']: test
            for test in self.tests
        }

        titles_of_common_tests = set(tests_by_titles.keys()).\
            intersection(check_objs_by_titles.keys())

        if titles_of_common_tests.__len__():
            LOG.debug("Next test results will be changed: {tests}".format(
                            tests="\n".join(titles_of_common_tests)))

        for title in titles_of_common_tests:
            self._check_errors(check_objs_by_titles[title],
                               tests_by_titles[title])

        # # Check regexp-style titles

        regexp_obj = [
            check_obj
            for check_obj in check_list_obj.attrs['tests']
            if check_obj.get('title_type', '') == 'regexp'
        ]
        for check_obj in regexp_obj:
            for test in self.tests:
                if test['title'] in titles_of_common_tests:
                    continue
                if self._match_found(check_obj['title'],
                                     test['title']):
                    LOG.debug(f"Found next test by regexp {test['title']}")
                    self._check_errors(check_obj, test)
