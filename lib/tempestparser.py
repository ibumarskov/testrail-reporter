from lib.reportparser import ReportParser

import xml.etree.ElementTree as ET


class TempestXMLParser(ReportParser):

    def __init__(self, xmlfile):
        tree = ET.parse(xmlfile)
        root = tree.getroot()

        self.suite_list = []
        self.report_list = []

        for child in root:
            if child.tag != 'testcase':
                continue
            tc = self.parse_tc_attr(child.attrib)
            section = self.choose_section_by_test_name(tc['title'])
            pos = self.get_section_position(section)
            self.suite_list[pos]['test_cases'].append(tc)

            tc_res = self.parse_tc_results_attr(child)
            self.report_list.append(tc_res)

    def get_section_position(self, name):
        for i, suite in enumerate(self.suite_list):
            if name == self.suite_list[i]['section_name']:
                return i
        self.suite_list.append({'section_name': name, 'test_cases': []})
        return self.get_section_position(name)

    def choose_section_by_test_name(self, tc_name):
        SECTIONS_MAP = {
            "Telemetry": ["telemetry_tempest_plugin."],
            "Glance": ["image."],
            "Keystone": ["identity."],
            "Neutron": ["network."],
            "Nova": ["compute."],
            "Swift": ["object_storage."],
            "Scenario": ["tempest.scenario."],
            "Manila": ["manila_tempest_tests"],
            "Ironic": ["ironic_tempest_plugin."],
            "Heat": ["heat_tempest_plugin."],
            "Designate": ["designate_tempest_plugin."],
            "Barbican": ["barbican_tempest_plugin."],
            "Horizon": ["tempest_horizon."],
            "Octavia": ["octavia_tempest_plugin."],
            "Tungsten": ["tungsten_tempest_plugin."]
        }

        for section, key_words in SECTIONS_MAP.items():
            for key_word in key_words:
                if key_word in tc_name:
                    return section
        return 'None'

    def parse_tc_attr(self, attributes):
        suite_attr_map = {
            'classname': ['title', 'custom_test_group'],
            'name': ['title', 'custom_test_case_description'],
            'time': ['estimate']
        }

        type_id_map = {'Automated': 1}
        qa_team_map = {'MOS': 4}
        priority_map = {'P0': 4}

        tc = {
            "title": '',
            "milestone_id": 66,
            # "section": section,
            "type_id": type_id_map['Automated'],
            "priority_id": priority_map['P0'],
            "estimate": '',
            "refs": '',
            "custom_qa_team": qa_team_map['MOS'],
            "custom_test_group": '',
            "custom_test_case_description": '',
            "custom_test_case_steps": [{"Run test": "passed"}],
            "custom_report_label": ''
        }
        for key, value in attributes.iteritems():
            if key in suite_attr_map.keys():
                item = suite_attr_map[key]
                for attr in item:
                    if tc[attr] != "":
                        tc[attr] = tc[attr] + '.' + value
                    else:
                        if attr == 'estimate':
                            # TO DO - fix bug TestRail API returned HTTP 400 ("Field :estimate is not in a valid time span format.")
                            continue
                            tc[attr] = value+'s'
                        else:
                            tc[attr] = value
        return tc

    def parse_tc_results_attr(self, child):
        result_attr_map = {
            'classname': ['title'],
            'name': ['title']
        }

        res = {
            "title": '',
            "status": 'passed',
            "comment": ''
        }

        for key, value in child.attrib.iteritems():
            if key in result_attr_map.keys():
                item = result_attr_map[key]
                for attr in item:
                    if res[attr] != "":
                        res[attr] = res[attr] + '.' + value
                    else:
                        res[attr] = value
        for obj in child:
            if obj.tag:
                res['status'] = obj.tag
                res['comment'] = obj.text
        return res
