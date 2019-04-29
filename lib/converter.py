from lib.testrailproject import TestRailProject


class Converter(object):

    def __init__(self, project):
        isinstance(project, TestRailProject)
        self.case_types = project.get_case_types()
        self.case_fields = project.get_case_fields()
        self.milestones = project.get_milestones_project()

    def casetype2id(self, test_case):
        for i in self.case_types:
            if test_case['type_id'] == i['name']:
                test_case['type_id'] = i['id']

    def milestone2id(self, test_case):
        for i in self.milestones:
            if test_case['milestone_id'] == i['name']:
                test_case['milestone_id'] = i['id']

