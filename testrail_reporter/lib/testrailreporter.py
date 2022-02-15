import copy
import logging
import sys

import pkg_resources
import yaml

from testrail_reporter.lib.exceptions import NotFound, Conflict
from testrail_reporter.lib.testrailproject import TestRailProject

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler(sys.stdout))


class TestRailReporter:

    def __init__(self, url, user, password, project_name, attr2id_map=None):
        self.project = TestRailProject(url, user, password, project_name)
        if not attr2id_map:
            rpath = '/'.join(('etc', 'attrs2id.yaml'))
            attr2id_map = pkg_resources.resource_filename("testrail_reporter",
                                                          rpath)
        with open(attr2id_map, 'r') as stream:
            self.attr2id_map = yaml.safe_load(stream)

    @staticmethod
    def _convert_test2id(result, tr_tests):
        for tr_res in tr_tests:
            if result['test_id'] == tr_res['title']:
                result['test_id'] = tr_res['id']
                return True
        raise NotFound("Can't find test: {}".format(result['test_id']))

    @staticmethod
    def match_group2tests(group, tr_tests):
        results = []
        for test in tr_tests:
            if group['test_id'] in test['title']:
                res = copy.copy(group)
                res['test_id'] = test['id']
                results.append(res)
        return results

    def _convert_casetype2id(self, test_case):
        for i in self.project.get_case_types():
            if test_case['type_id'] == i['name']:
                test_case['type_id'] = i['id']
                return True
        raise NotFound("Can't find Case Type '{}'"
                       "".format(test_case['type_id']))

    def _convert_milestone2id(self, test_case):
        for i in self.project.milestones:
            if test_case['milestone_id'] == i['name']:
                test_case['milestone_id'] = i['id']
                return True
        raise NotFound("Can't find Milestone '{}'"
                       "".format(test_case['milestone_id']))

    def _convert_priority2id(self, test_case):
        for p in self.project.priorities:
            if test_case['priority_id'] == p['name']:
                test_case['priority_id'] = p['id']
                return True
        raise NotFound("Can't find Priority '{}'"
                       "".format(test_case['priority_id']))

    def convert_customfield2id(self, tc, field_name):
        items = None
        for field in self.project.case_fields:
            if field['system_name'] == field_name:
                items = field['configs'][0]['options']['items']
                break
        if not items:
            raise NotFound("Can't find custom filed: {}".format(field_name))
        for item in items.split('\n'):
            i, name = item.split(',')
            if tc[field_name] == name.strip():
                tc[field_name] = i
                break

    def _convert_status2id(self, result):
        for s in self.project.statuses:
            if result['status_id'].lower() == s['label'].lower():
                result['status_id'] = s['id']
                return True
        raise NotFound("Can't find status: {}".format(result['status_id']))

    def get_section_id(self, name, suite):
        for i in self.project.get_sections_project(suite['id']):
            if name == i['name']:
                return i['id']
        raise NotFound("Can't find Section '{}' in Test Suite '{}'"
                       "".format(name, suite['name']))

    def get_milestone_id(self, name):
        for m in self.project.milestones:
            if m['name'] == name:
                return m['id']
        raise NotFound("Can't find milestone: {}".format(name))

    def update_test_suite(self, name, tc_list):
        # Check suite name and create if needed:
        try:
            suite = self.project.get_suite_by_name(name)
        except NotFound:
            suite_data = {"name": name}
            suite = self.project.add_suite_project(suite_data)
        suite_id = suite['id']

        # Exclude existing cases for fast processing
        LOG.info("Exclude existing cases for fast processing:\n"
                 "Amount of test cases: {}".format(len(tc_list)))
        cases = self.project.get_cases_project(suite_id=suite_id)
        casetitles = [x['title'] for x in cases]
        tc_list = [tc for tc in tc_list if tc['title'] not in casetitles]
        LOG.info("Remaining amount of test cases: {}".format(len(tc_list)))

        tr_cases = {}
        for tc in tc_list:
            # Remove section_id from dict and convert it to id if necessary
            section_id = tc.pop('section_id')
            if isinstance(section_id, str):
                try:
                    section_id = self.get_section_id(section_id, suite)
                except NotFound:
                    section_data = {'name': section_id,
                                    'suite_id': suite_id}
                    LOG.info("Create section: {}".format(section_id))
                    self.project.add_section_project(section_data)
                    section_id = self.get_section_id(section_id, suite)

            if isinstance(tc['type_id'], str) and tc['type_id']:
                self._convert_casetype2id(tc)
            if isinstance(tc['milestone_id'], str) and tc['milestone_id']:
                self._convert_milestone2id(tc)
            if isinstance(tc['priority_id'], str) and tc['priority_id']:
                self._convert_priority2id(tc)

            # Convert custom attributes to id
            for custom in self.attr2id_map['attributes2id']:
                if custom in tc:
                    self.convert_customfield2id(tc, custom)
                else:
                    LOG.warning("Custom field '{}' isn't in the case "
                                "attributes".format(custom))

            if section_id not in tr_cases:
                tr_cases[section_id] = {}
                tr_cases[section_id]['cases'] = \
                    self.project.get_cases_project(suite_id, section_id)
                tr_cases[section_id]['titles'] = []
                for tr_tc in tr_cases[section_id]['cases']:
                    tr_cases[section_id]['titles'].append(tr_tc['title'])

            if tc['title'] not in tr_cases[section_id]['titles']:
                LOG.info("Create case: {}".format(tc['title']))
                self.project.add_case(section_id, tc)

    def publish_results(self, results, plan_name, suite_name, run_name,
                        milestone=None, configuration=None,
                        update_existing=False, remove_untested=False,
                        remove_skipped=False, limit=0):
        suite = self.project.get_suite_by_name(suite_name)
        plans_list = self.project.get_plans_project()
        plan = None
        milestone_id = None
        conf_ids = []
        if configuration:
            isinstance(configuration, dict)
            conf_ids = self.project.get_config_ids(configuration)
            conf_ids.sort()
        if milestone:
            milestone_id = self.get_milestone_id(milestone)
        for p in plans_list:
            if p['name'] == plan_name and p['milestone_id'] == milestone_id:
                plan = self.project.get_plan(p['id'])
                break
        if plan is None:
            LOG.info("TestPlan wasn't found and will be created.")
            plan_data = {'name': plan_name, 'milestone_id': milestone_id}
            plan = self.project.add_plan_project(plan_data)
        LOG.info("TestPlan url: {}".format(plan['url']))

        run_present = False
        for r in plan['entries']:
            if run_name == r['name']:
                if r['runs'][0]["config_ids"] != conf_ids:
                    continue
                run_present = True
                plan_entry = r
                if not update_existing:
                    raise Conflict("Test Run {} already present. Link: {}"
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
            LOG.info("Test Run {} has been created".format(
                plan_entry['runs'][0]['url']))

        run = self.project.get_run(plan_entry['runs'][0]['id'])
        tr_tests = list(self.project.get_tests(run['id']))

        # Analysis of TearDown actions should be processed for raw results to
        # exclude false results for untested test cases.
        for res_td in results['results_teardown']:
            for res in results['results']:
                if res_td['test_id'] in res['test_id']:
                    res['comment'] += "=================================\n"
                    res['comment'] += "Some TearDown actions are failed:\n"
                    res['comment'] += "=================================\n"
                    res['comment'] += res_td['comment']
                    LOG.warning("TestCase {} has failed TearDown action. "
                                "Please check logs.".format(res['test_id']))

        for res in results['results']:
            if isinstance(res['test_id'], str):
                self._convert_test2id(res, tr_tests)
            if isinstance(res['status_id'], str):
                self._convert_status2id(res)
            if limit and len(res['comment']) > limit:
                LOG.info("Test {}: cutting the length of the comments to {} "
                         "bytes due to capacity limit."
                         "".format(res['test_id'], limit))
                lim = int(limit/2)
                separator = "< ----- logs were omitted due to limit ----- >"
                res['comment'] = "\n".join([res['comment'][:lim], separator,
                                            res['comment'][-lim:]])

        for res in results['results_setup']:
            if isinstance(res['status_id'], str):
                self._convert_status2id(res)
            results_setup = self.match_group2tests(res, tr_tests)
            results['results'].extend(results_setup)

        self.project.add_results(run['id'], {'results': results['results']})
        LOG.info("Results were uploaded.")

        rm_statuses = []
        if remove_skipped:
            rm_statuses.append("skipped")
        if remove_untested:
            rm_statuses.append("untested")
        if rm_statuses:
            LOG.info("Remove tests with statuses: {}".format(rm_statuses))
            rm_tests = self.get_tests_by_status(run['id'], rm_statuses)
            case_ids = list(map(lambda a: a['case_id'], rm_tests))
            data = {'include_all': False,
                    'case_ids': case_ids}
            if configuration:
                data["config_ids"] = conf_ids
            self.project.update_plan_entry(plan['id'], plan_entry['id'], data)
        LOG.info("Completed.")

    def get_tests_by_status(self, run_id, statuses):
        status_ids = list(map(lambda a: a['id'], self.project.statuses))
        for status in statuses:
            status_ids.remove(self.project.get_status_by_label(status))
        tests_filter = self.project.get_tests_filter(status_id=status_ids)
        return list(self.project.get_tests(run_id, filter=tests_filter))
