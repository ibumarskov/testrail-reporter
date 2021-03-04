import copy
import yaml
import re
from testrail_reporter.lib.actions import perform_actions


class TestCaseParser(object):
    def __init__(self, tr_case_attrs, tr_case_map):
        with open(tr_case_attrs, 'r') as stream:
            self.tr_case_attrs = yaml.safe_load(stream)
        with open(tr_case_map, 'r') as stream:
            self.tr_case_map = yaml.safe_load(stream)

    def get_tc_list(self, tc_list_file):
        with open(tc_list_file, 'r') as stream:
            tc_raw_list = [line.rstrip('\n') for line in stream]
        tc_list = []
        for i in tc_raw_list:
            tc = copy.copy(self.tr_case_attrs)
            tc['title'] = perform_actions(
                i, self.tr_case_map['title']['actions'])
            assert tc['title'] is not None, "Title shouldn't be empty"
            section_id = perform_actions(
                i, self.tr_case_map['section']['actions'])
            if section_id:
                tc['section_id'] = section_id

            pattern = r"([\b\w\.]+)\."
            m_tg = re.match(pattern, tc['title'])
            tc['custom_test_group'] = m_tg.group(1)

            pattern = r".+id-([\b\w\-]+)"
            m_id = re.match(pattern, tc['title'])
            try:
                tc['custom_report_label'] = m_id.group(1)
            except AttributeError:
                print("custom_report_label is absent")
                print(tc['title'])

            # pattern = r".+\.(\w+\[[\w\d\-,]+\])"
            pattern = r".+\.(\w+[\w\d\-,\[\]]+)"
            m_dscr = re.match(pattern, tc['title'])
            tc['custom_test_case_description'] = m_dscr.group(1)
            tc_list.append(tc)
        return tc_list
