from lib.testrailproject import TestRailProject
from lib.tempestparser import ReportParser

import yaml


class TestRailReporter:
    complexity_map = {
        'smoke': 1,
        'core': 2,
        'advanced': 3
    }

    def __init__(self, project, report_obj,
                 attr2id_map='etc/attrs2id.yaml'):
        isinstance(project, TestRailProject)
        isinstance(report_obj, ReportParser)
        # self.project = TestRailProject()
        self.project = project
        self.suite_list = report_obj.suite_list
        self.result_list = report_obj.result_list
        self.case_types = project.get_case_types()
        self.case_fields = project.get_case_fields()
        self.milestones = project.get_milestones_project()
        with open(attr2id_map, 'r') as stream:
            self.attr2id_map = yaml.load(stream)

    def convert_casetype2id(self, test_case):
        for i in self.case_types:
            if test_case['type_id'] == i['name']:
                test_case['type_id'] = i['id']

    def convert_milestone2id(self, test_case):
        for i in self.milestones:
            if test_case['milestone_id'] == i['name']:
                test_case['milestone_id'] = i['id']

    def update_test_suite(self, suite_name):
        # Check suite name and create if needed:
        try:
            suite_id = self.project.get_suite_by_name(suite_name)['id']
        except:
            suite_id = self.project.add_suite_project(suite_name)

        tr_sections = self.project.get_sections_project(suite_id)

        for section in self.suite_list:
            # TO DO - fix tests without section
            tr_section = None
            for tr_s in tr_sections:
                if tr_s['name'] == section['section_name']:
                    tr_section = tr_s

            if not tr_section:
                data = {'suite_id': suite_id, 'name': section['section_name']}
                self.project.add_section_project(data)
                tr_section = self.project.get_section_by_name(
                    suite_id, section['section_name'])

            tr_tests = self.project.get_cases_project(suite_id,
                                                      tr_section['id'])

            titles_list = []
            for tr_t in tr_tests:
                titles_list.append(tr_t['title'])

            for testcase in section['test_cases']:
                if testcase['title'] not in titles_list:
                    self.convert_casetype2id(testcase)
                    self.convert_milestone2id(testcase)
                    self.project.add_case(tr_section['id'], testcase)

    def report_test_plan(self, plan_name, suite_name, run_name,
                         update_existing=False):
        suite = self.project.get_suite_by_name(suite_name)
        plans_list = self.project.get_plans_project()
        plan = None

        for p in plans_list:
            if p['name'] == plan_name:
                plan = self.project.get_plan(p['id'])
        if plan is None:
            plan_data = {'name': plan_name}
            plan = self.project.add_plan_project(plan_data)

        run_present = False
        for r in plan['entries']:
            if run_name == r['name']:
                run_present = True
                plan_entry = r
                if not update_existing:
                    raise Exception("Test Run {} already present. Link: {}"
                                    "".format(run_name,
                                              plan_entry['runs'][0]['url']))
                else:
                    print "Test Run {} will be overridden".format(
                        plan_entry['runs'][0]['url'])
        if not run_present:
            run_data = {'suite_id': suite['id'], 'name': run_name}
            plan_entry = self.project.add_plan_entry(plan['id'], run_data)

        run = self.project.get_run(plan_entry['runs'][0]['id'])
        test_results = self.project.get_tests(run['id'])
        results = {'results': []}
        for r in self.result_list:
            result = self.parse_report_attr(r, test_results)
            results['results'].append(result)

        self.project.add_results(run['id'], results)

    def parse_report_attr(self, report, test_results):
        result = {
            'test_id': '',
            'status_id': '',
            'comment': '',
        }

        # Only lower case !
        status_map = {
            'passed': 1,
            'blocked': 2,
            'untested': 3,
            'other': 4,
            'failed': 5,
            'skipped': 6,
            'in progress': 7,
            'prodfailed': 8,
            'testfailed': 9,
            'infrafailed': 10,
            'fixed': 11,
            'regression': 12,
            'failure': 5
        }

        attr_map = {
            'comment': ['comment']
        }

        for res in test_results:
            if report['title'] == res['title']:
                result['test_id'] = res['id']
        if not result['test_id']:
            raise Exception('Can not found test case with name "{}"'
                            ''.format(report['title']))

        result['status_id'] = status_map[report['status'].lower()]

        for key, value in report.iteritems():
            if key in attr_map.keys():
                item = attr_map[key]
                for attr in item:
                    if result[attr] != "":
                        result[attr] = result[attr] + '.' + value
                    else:
                        result[attr] = value
        return result
