import logging
import yaml

from lib.testrailproject import TestRailProject

LOG = logging.getLogger(__name__)


class TestRailReporter:
    complexity_map = {
        'smoke': 1,
        'core': 2,
        'advanced': 3
    }

    def __init__(self, url, user, password, project_name,
                 attr2id_map='etc/attrs2id.yaml'):
        self.project = TestRailProject(url, user, password, project_name)
        with open(attr2id_map, 'r') as stream:
            self.attr2id_map = yaml.safe_load(stream)

        # self.suite_list = report_obj.suite_list
        # self.result_list = report_obj.result_list
        # self.result_list_setUpClass = report_obj.result_list_setUpClass
        # self.case_types = project.get_case_types()
        # self.case_fields = project.get_case_fields()

    def update_test_suite(self, name, tc_list):
        # Check suite name and create if needed:
        try:
            suite = self.project.get_suite_by_name(name)
        except Exception:
            suite_data = {"name": name}
            suite = self.project.add_suite_project(suite_data)
        suite_id = suite['id']
        tr_sections = self.project.get_sections_project(suite_id)

        # Add case without section
        tr_cases = {}
        for tc in tc_list:
            # Remove section_id from dict and convert it to id if necessary
            section_id = tc.pop('section_id')
            if isinstance(section_id, str):
                try:
                    section_id = self.get_section_id(section_id, suite)
                except Exception:
                    section_data = {'name': section_id,
                                    'suite_id': suite_id}
                    self.project.add_section_project(section_data)
                    section_id = self.get_section_id(section_id, suite)

            if isinstance(tc['type_id'], str):
                self.convert_casetype2id(tc)
            if isinstance(tc['milestone_id'], str):
                self.convert_milestone2id(tc)

            if section_id not in tr_cases:
                tr_cases[section_id] = {}
                tr_cases[section_id]['cases'] = \
                    self.project.get_cases_project(suite_id, section_id)
                tr_cases[section_id]['titles'] = []
                for tr_tc in tr_cases[section_id]['cases']:
                    tr_cases[section_id]['titles'].append(tr_tc['title'])

            if tc['title'] not in tr_cases[section_id]['titles']:
                self.project.add_case(section_id, tc)

    def convert_casetype2id(self, test_case):
        for i in self.project.get_case_types():
            if test_case['type_id'] == i['name']:
                test_case['type_id'] = i['id']
                return True
        raise Exception("Can't find Case Type '{}'"
                        "".format(test_case['type_id']))

    def convert_milestone2id(self, test_case):
        for i in self.project.milestones:
            if test_case['milestone_id'] == i['name']:
                test_case['milestone_id'] = i['id']
                return True
        raise Exception("Can't find Milestone '{}'"
                        "".format(test_case['milestone_id']))

    def get_section_id(self, name, suite):
        sections = self.project.get_sections_project(suite['id'])
        for i in sections:
            if name == i['name']:
                return i['id']
        raise Exception("Can't find Section '{}' in Test Suite '{}'"
                        "".format(name, suite['name']))

    def get_config_id(self, group, conf):
        for tr_group in self.project.configurations:
            if tr_group["name"] == group:
                for tr_conf in tr_group["configs"]:
                    if tr_conf["name"] == conf:
                        return tr_conf["id"]
        raise Exception("Can't find configuration for plan entry:\n"
                        "{}:{}".format(group, conf))

    def get_milestone_id(self, name):
        for m in self.project.milestones:
            if m['name'] == name:
                return m['id']
        raise Exception("Can't find milestone {}".format(name))

    def report_test_plan(self, plan_name, suite_name, run_name,
                         milestone=None, configuration=None,
                         update_existing=False, remove_untested=False):
        suite = self.project.get_suite_by_name(suite_name)
        plans_list = self.project.get_plans_project()
        plan = None
        milestone_id = None
        conf_ids = []
        if configuration:
            isinstance(configuration, dict)
            for k, v in configuration.iteritems():
                conf_ids.append(self.get_config_id(k, v))
        if milestone:
            milestone_id = self.get_milestone_id(milestone)
        for p in plans_list:
            if p['name'] == plan_name and p['milestone_id'] == milestone_id:
                plan = self.project.get_plan(p['id'])
        if plan is None:
            plan_data = {'name': plan_name, 'milestone_id': milestone_id}
            plan = self.project.add_plan_project(plan_data)

        run_present = False
        for r in plan['entries']:
            if run_name == r['name']:
                if r['runs'][0]["config_ids"] != conf_ids:
                    continue
                run_present = True
                plan_entry = r
                if not update_existing:
                    raise Exception("Test Run {} already present. Link: {}"
                                    "".format(run_name,
                                              plan_entry['runs'][0]['url']))
                else:
                    LOG.warning("Test Run {} will be overridden".format(
                        plan_entry['runs'][0]['url']))
        if not run_present:
            run_data = {'suite_id': suite['id'], 'name': run_name}
            if configuration:
                run_data["config_ids"] = conf_ids
                run_data["runs"] = [{"config_ids": conf_ids}]
            plan_entry = self.project.add_plan_entry(plan['id'], run_data)

        run = self.project.get_run(plan_entry['runs'][0]['id'])
        test_results = self.project.get_tests(run['id'])
        results = {'results': []}
        for r in self.result_list:
            result = self.parse_report_attr(r, test_results)
            results['results'].append(result)
        for r in self.result_list_setUpClass:
            lls = self.match_group2tests(r, test_results)
            results['results'].extend(lls)
            pass

        self.project.add_results(run['id'], results)

        if remove_untested:
            untested_tests = self.get_untested_tests(run['id'])
            case_ids = map(lambda a: a['case_id'], untested_tests)
            data = {'include_all': False,
                    'case_ids': case_ids}
            if configuration:
                data["config_ids"] = conf_ids
            self.project.update_plan_entry(plan['id'], plan_entry['id'], data)

    def match_group2tests(self, report, test_results):
        results = []
        for t in test_results:
            if report['group'] in t['title']:
                result = self.parse_report_attr(report, [t])
                results.append(result)
        return results

    def get_untested_tests(self, run_id):
        status_ids = map(lambda a: a['id'], self.project.statuses)
        status_ids.remove(self.project.get_status_by_label("untested"))
        tests_filter = self.project.get_tests_filter(status_id=status_ids)
        return self.project.get_tests(run_id, filter=tests_filter)

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
            if 'group' in report.keys():
                if report['group'] in res['title']:
                    result['test_id'] = res['id']
                    break
            if report['title'] == res['title']:
                result['test_id'] = res['id']
                break
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
