import logging
import sys

from testrail_reporter.lib.exceptions import NotFound
from testrail_reporter.lib.testrail import TestRailAPICalls

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler(sys.stdout))


class TestRailProject(TestRailAPICalls):
    def __init__(self, url, user, password, project_name, fuse=True):
        super(TestRailProject, self).__init__(url, user, password)
        self.project = self._get_project_by_name(project_name)
        self.statuses = self.get_statuses()
        milestone_f = self.get_milestones_filter(is_completed=False,
                                                 is_started=True)
        self.milestones = list(self.get_milestones_project(milestone_f))
        self.configurations = self.get_configs_project()
        self.case_fields = self.get_case_fields()
        self.result_fields = self.get_result_fields()
        self.priorities = self.get_priorities()
        self.fuse = fuse

    def _get_project_by_name(self, project_name):
        for project in self.get_projects():
            if project['name'] == project_name:
                return project
        return None

    @staticmethod
    def _fuse():
        LOG.warning("DO NOT TRY TO DO IT !!!")

    def get_projects(self):
        yield from self._get_all(
            super(TestRailProject, self).get_projects(), 'projects')

    def get_cases(self, project_id, suite_id=None, section_id=None):
        yield from self._get_all(
            super(TestRailProject, self).get_cases(
                self.project['id'], suite_id, section_id), 'cases')

    def get_milestones(self, project_id, filter=None):
        yield from self._get_all(
            super(TestRailProject, self).get_milestones(project_id, filter),
            'milestones')

    def get_plans(self, project_id, filter=None):
        yield from self._get_all(
            super(TestRailProject, self).get_plans(project_id, filter),
            'plans')

    def get_results(self, test_id, filter=None):
        yield from self._get_all(
            super(TestRailProject, self).get_results(test_id, filter),
            'results')

    def get_results_for_case(self, run_id, case_id, filter=None):
        yield from self._get_all(
            super(TestRailProject, self).get_results_for_case(
                run_id, case_id, filter), 'results')

    def get_results_for_run(self, run_id, filter=None):
        yield from self._get_all(
            super(TestRailProject, self).get_results_for_run(run_id, filter),
            'results')

    def get_runs(self, project_id, filter=None):
        yield from self._get_all(
            super(TestRailProject, self).get_runs(project_id, filter), 'runs')

    def get_sections(self, project_id, suite_id):
        yield from self._get_all(
            super(TestRailProject, self).get_sections(project_id, suite_id),
            'sections')

    def get_tests(self, run_id, filter=None):
        yield from self._get_all(
            super(TestRailProject, self).get_tests(run_id, filter), 'tests')

    def _get_all(self, response, entity):
        for ent in response[entity]:
            yield ent
        while response["_links"]["next"]:
            uri = response["_links"]["next"].replace("/api/v2/", '')
            response = self.client.send_get(uri)
            for ent in response[entity]:
                yield ent

    def get_cases_project(self, suite_id=None, section_id=None):
        return self.get_cases(self.project['id'], suite_id, section_id)

    def get_configs_project(self):
        return super(TestRailProject, self).get_configs(self.project['id'])

    def add_config_group_project(self, data):
        return super(TestRailProject, self).add_config_group(
            self.project['id'], data)

    def get_milestones_project(self, filter=None):
        return self.get_milestones(self.project['id'], filter)

    def get_plans_project(self, filter=None):
        return self.get_plans(self.project['id'], filter)

    def add_plan_project(self, data):
        return super(TestRailProject, self).add_plan(self.project['id'], data)

    def get_current_project(self):
        return super(TestRailProject, self).get_project(self.project['id'])

    def update_current_project(self, data):
        return super(TestRailProject, self).update_project(self.project['id'],
                                                           data)

    def delete_current_project(self):
        if self.fuse is False:
            return super(TestRailProject, self).delete_project(
                self.project['id'])
        else:
            self._fuse()

    def get_runs_project(self, filter=None):
        return self.get_runs(self.project['id'], filter)

    def add_run_project(self, data):
        return super(TestRailProject, self).add_run(self.project['id'], data)

    def get_sections_project(self, suite_id):
        return self.get_sections(self.project['id'], suite_id)

    def add_section_project(self, data):
        return super(TestRailProject, self).add_section(self.project['id'],
                                                        data)

    def get_suites_project(self):
        return super(TestRailProject, self).get_suites(self.project['id'])

    def add_suite_project(self, data):
        return super(TestRailProject, self).add_suite(self.project['id'],
                                                      data)

    def get_templates_project(self):
        return super(TestRailProject, self).get_templates(self.project['id'])

    def get_suite_by_name(self, name):
        for suite in self.get_suites_project():
            if suite['name'] == name:
                return self.get_suite(suite_id=suite['id'])
        raise NotFound("Suite {}".format(name))

    def get_section_by_name(self, suite_id, section_name):
        for section in self.get_sections_project(suite_id=suite_id):
            if section['name'] == section_name:
                return self.get_section(section_id=section['id'])

    def get_milestone_by_name(self, name):
        for m in self.get_milestones_project():
            if m['name'] == name:
                return self.get_milestone(m['id'])

    def get_submilestones(self, milestone_name):
        submilestones = []
        milestone = self.get_milestone_by_name(milestone_name)
        for sub in milestone['milestones']:
            submilestones.append(sub['name'])
        return submilestones

    def get_plan_by_name(self, name):
        for plan in self.get_plans_project():
            if plan['name'] == name:
                return self.get_plan(plan_id=plan['id'])
        raise NotFound("TestPlan {}".format(name))

    def get_run_by_name(self, name):
        for run in self.get_runs_project():
            if run['name'] == name:
                return self.get_run(run_id=run['id'])
        raise NotFound("TestRun {}".format(name))

    def get_status_by_label(self, label):
        for status in self.statuses:
            if status['label'].lower() == label.lower():
                return status['id']
        raise NotFound("Status {}".format(label))

    def get_config_id(self, group, conf):
        for tr_group in self.configurations:
            if tr_group["name"] == group:
                for tr_conf in tr_group["configs"]:
                    if tr_conf["name"] == conf:
                        return tr_conf["id"]
        raise NotFound("Can't find configuration for plan entry:\n"
                       "{}:{}".format(group, conf))

    def get_config_ids(self, conf_dict):
        conf_ids = []
        for group, conf in conf_dict.items():
            conf_ids.append(self.get_config_id(group, conf))
        return conf_ids

    @staticmethod
    def result_data(status_id, comment=None, version=None, elapsed=None,
                    defects=None, assignedto_id=None):
        data = {'status_id': status_id}
        if comment:
            data['comment'] = comment
        if defects:
            data['defects'] = defects
        return data
