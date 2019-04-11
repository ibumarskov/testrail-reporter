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
        self.tests = None

    def filter_by_status(self, statuses=[]):
        filter = self.project.get_tests_filter(status_id=[5])
        self.tests = self.project.get_tests(self.test_run['id'], filter=filter)

    def _check_errors(self, check_obj):
        for err in check_obj['errors']:

            pass

    def analyze_results(self, check_list_obj):
        isinstance(check_list_obj, CheckListParser)
        for check_obj in check_list_obj:
            for test in self.tests:
                self._check_errors(test)
