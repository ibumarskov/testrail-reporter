import copy
import re
import yaml


class TestListParser(object):
    def __init__(self, tc_list_file,
                 tr_case_attrs='etc/tr_case_attrs.yaml',
                 case_map='etc/maps/pytest/testlist_map.yaml'):
        with open(tr_case_attrs, 'r') as stream:
            self.tr_case_attrs = yaml.safe_load(stream)
        with open(case_map, 'r') as stream:
            self.case_map = yaml.safe_load(stream)
        with open(tc_list_file, 'r') as stream:
            self.tc_raw_list = [line.rstrip('\n') for line in stream]
        self.tc_list = []
        for i in self.tc_raw_list:
            tc = copy.copy(self.tr_case_attrs)
            tc['title'] = self._parse(i, self.case_map['title'])
            assert tc['title'] is not None, "Title shouldn't be empty"
            tc['section_id'] = self._parse(i, self.case_map['section'])
            self.tc_list.append(tc)

    @staticmethod
    def _parse(string, actions):
        f = re.findall(actions['find'], string)
        if not f:
            return None
        elif len(f) > 1:
            Exception("Was find more than one match: {}".format(s))
        else:
            s = f[0]
        if 'replace' in actions:
            s = s.replace(actions['replace']['old'], actions['replace']['new'])
        return s

    def _parse_title(self, string):
        s = re.findall(self.case_map['title']['find'], string)
        return s[0]

    def _parse_section(self, string):
        s = re.findall(self.case_map['section']['find'], string)
        if s:
            return s[0]
        else:
            return None
