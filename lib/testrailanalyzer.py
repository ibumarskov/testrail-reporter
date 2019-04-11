from lib.testrailproject import TestRailProject
from lib.reportparser import CheckListParser


class TestRailAnalyzer:
    complexity_map = {
        'smoke': 1,
        'core': 2,
        'advanced': 3
    }

    def __init__(self, project, test_run, test_plan=None):
        isinstance(project, TestRailProject)
        # self.project = TestRailProject()
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
        id = self.project.get_status_by_name("failed")
        filter = self.project.get_tests_filter(status_id=[id])
        return self.project.get_tests(self.test_run['id'], filter=filter)

    def _check_errors(self, check_obj, test):
        case_res = self.project.get_results_for_case(test['run_id'],
                                                     test['case_id'])
        pass
        for err in check_obj['errors']:
            pass

    def analyze_results(self, check_list_obj):
        isinstance(check_list_obj, CheckListParser)
        for check_obj in check_list_obj.attrs['tests']:
            for test in self.tests:
                if test['title'] == check_obj['title']:
                    self._check_errors(check_obj, test)
