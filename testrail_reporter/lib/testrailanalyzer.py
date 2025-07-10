import html
import logging
import sys

import yaml

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
        return list(self.project.get_tests(self.test_run['id'],
                                           filter=tests_filter))

    def _check_errors(self, check_obj, test):
        test_res = list(self.project.get_results(test['id']))
        current_res = test_res[-1]
        if check_obj['errors']:
            for err in check_obj['errors']:
                if not current_res['comment']:
                    LOG.warning("Test result for {} doesn't contain any log."
                                "".format(test["title"]))
                    return False
                if err in html.unescape(current_res['comment']):
                    pass
                else:
                    LOG.info("Can't find string: {}".format(err))
                    LOG.warning("Test results for {} don't match know issue."
                                "".format(test["title"]))
                    return False
        msg = "Set by result analyzer"
        status = self.project.get_status_by_label(check_obj['status'])
        defects = check_obj['defects']
        data = self.project.result_data(status, comment=msg, defects=defects)
        self.project.add_result(test['id'], data)
        LOG.info("Test '{}' set to {}".format(test["title"],
                                              check_obj['status']))

    def analyze_results(self, check_list_obj):
        isinstance(check_list_obj, CheckListParser)
        for test in self.tests:
            for check_obj in check_list_obj.attrs['tests']:
                if test['title'] == check_obj['title']:
                    self._check_errors(check_obj, test)


class Analyzer(object):
    def __init__(self, check_list):
        with open(check_list, 'r') as stream:
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

    def _check_errors(self, check_obj, test_result):
        if check_obj['errors']:
            for err in check_obj['errors']:
                if not test_result['comment']:
                    LOG.warning(f"Test result for {test_result['test_id']} doesn't contain any log.")
                    return False
                if err in html.unescape(test_result['comment']):
                    pass
                else:
                    LOG.info("Can't find string: {}".format(err))
                    LOG.warning(f"Test results for {test_result['test_id']} don't match know issue.")
                    return False
        LOG.info(f"Test {test_result['test_id']} set to {check_obj['status']}")
        return True

    def analyze(self, test_results):
        # Analyze list of failed test cases and return modified list with detected issues
        unprocessed = []
        for test_res in test_results:
            for check_obj in self.attrs['tests']:
                if test_res['test_id'] == check_obj['title']:
                    if not self._check_errors(check_obj, test_res):
                        unprocessed.append(test_res)
                    break
            else:
                LOG.warning(f"Test {test_res['test_id']} wasn't find in test analyzer list.")
                unprocessed.append(test_res)
        return unprocessed
