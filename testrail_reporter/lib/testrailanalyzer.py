import logging
import yaml

from testrail_reporter.lib.testrailproject import TestRailProject

LOG = logging.getLogger(__name__)


class CheckListParser(object):
    def __init__(self, check_list_attrs='etc/check_list_example.yaml'):
        with open(check_list_attrs, 'r') as stream:
            self.attrs = yaml.safe_load(stream)
        self._check_structure()

    def _check_structure(self):
        for test in self.attrs['tests']:
            if 'title' not in test:
                raise Exception("title not found")
            if 'status' not in test:
                raise Exception("status not found")
            if 'errors' not in test:
                test['errors'] = None
            if 'defects' not in test:
                test['defects'] = None


class TestRailAnalyzer:

    def __init__(self, project, test_run, test_plan=None):
        isinstance(project, TestRailProject)
        self.project = project
        if test_plan:
            self.test_plan = self.project.get_plan_by_name(test_plan)
            for run in self.test_plan['entries']:
                if test_run == run['name']:
                    self.test_run = self.project.get_run(run['runs'][0]['id'])
        else:
            self.test_run = self.project.get_run_by_name(test_run)
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
                    LOG.warn("Test result for {} doesn't contain any log."
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

    def analyze_results(self, check_list_obj):
        isinstance(check_list_obj, CheckListParser)
        for check_obj in check_list_obj.attrs['tests']:
            for test in self.tests:
                if test['title'] == check_obj['title']:
                    self._check_errors(check_obj, test)
