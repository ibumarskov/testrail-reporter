import logging

from testrail_reporter.lib.exceptions import NotFound
from testrail_reporter.lib.testrail import TestRailAPICalls

LOG = logging.getLogger(__name__)


class TestRailProject(TestRailAPICalls):
    def __init__(self, url, user, password, project_name, fuse=True):
        super(TestRailProject, self).__init__(url, user, password)
        self.project = self._get_project_by_name(project_name)
        self.statuses = self.get_statuses()
        milestone_f = self.get_milestones_filter(is_completed=False,
                                                 is_started=True)
        self.milestones = self.get_milestones_project(milestone_f)
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

    def get_cases_project(self, suite_id=None, section_id=None):
        return super(TestRailProject, self).get_cases(self.project['id'],
                                                      suite_id,
                                                      section_id)

    def get_configs_project(self):
        return super(TestRailProject, self).get_configs(self.project['id'])

    def add_config_group_project(self, data):
        return super(TestRailProject, self).add_config_group(
            self.project['id'], data)

    def get_milestones_project(self, filter=None):
        return super(TestRailProject, self).get_milestones(self.project['id'],
                                                           filter)

    def get_plans_project(self, filter=None):
        return super(TestRailProject, self).get_plans(self.project['id'],
                                                      filter)

    def add_plan_project(self, data):
        return super(TestRailProject, self).add_plan(self.project['id'],
                                                     data)

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
        return super(TestRailProject, self).get_runs(self.project['id'],
                                                     filter)

    def add_run_project(self, data):
        return super(TestRailProject, self).add_run(self.project['id'], data)

    def get_sections_project(self, suite_id):
        return super(TestRailProject, self).get_sections(self.project['id'],
                                                         suite_id)

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

    @staticmethod
    def result_data(status_id, comment=None, version=None, elapsed=None,
                    defects=None, assignedto_id=None):
        data = {'status_id': status_id}
        if comment:
            data['comment'] = comment
        if defects:
            data['defects'] = defects
        return data
