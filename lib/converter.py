from lib.testrailproject import TestRailProject


class Converter(object):

    def __init__(self, project):
        isinstance(project, TestRailProject)
        self.case_types = project.case_types
        self.case_fields = project.case_fields
        self.statuses = project.statuses
        self.milestones = project.milestones

    def casetype2id(self, test_case):
        for i in self.case_types:
            if test_case['type_id'] == i['name']:
                test_case['type_id'] = i['id']
        raise Exception("CaseType {} not found".format(test_case['type_id']))

    def milestone2id(self, test_case):
        for i in self.milestones:
            if test_case['milestone_id'] == i['name']:
                test_case['milestone_id'] = i['id']
        raise Exception("Milestone {} not found".format(
            test_case['milestone_id']))
