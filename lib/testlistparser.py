import copy
import re
import yaml

from lib.actions import perform_actions


class TestListParser(object):
    def __init__(self,
                 tr_case_attrs='etc/tr_case_attrs.yaml',
                 case_map='etc/maps/pytest/name_template.yaml'):
        with open(tr_case_attrs, 'r') as stream:
            self.tr_case_attrs = yaml.safe_load(stream)
        with open(case_map, 'r') as stream:
            self.case_map = yaml.safe_load(stream)

    def get_tc_list(self, tc_list_file):
        with open(tc_list_file, 'r') as stream:
            tc_raw_list = [line.rstrip('\n') for line in stream]
        tc_list = []
        for i in tc_raw_list:
            tc = copy.copy(self.tr_case_attrs)
            tc['title'] = perform_actions(i, self.case_map['title']['actions'])
            assert tc['title'] is not None, "Title shouldn't be empty"
            section_id = perform_actions(i, self.case_map['section']['actions'])
            if section_id:
                tc['section_id'] = section_id
            tc_list.append(tc)
        return tc_list
