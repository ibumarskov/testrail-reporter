import logging
import re
import sys
import xml.etree.ElementTree as ET
import yaml

from testrail_reporter.lib.actions import perform_actions
from testrail_reporter.lib.exceptions import UnknownAction, ActionIsMissed, \
    FieldIsMissed


LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler(sys.stdout))


class ReportParser(object):
    def __init__(self, tr_result_attrs):
        with open(tr_result_attrs, 'r') as stream:
            self.tr_result_attrs = yaml.safe_load(stream)
        self.raw_results = []

    def process_testsuite(self, root):
        assert root.tag == 'testsuite', \
            f"Expected <testsuite> but received <{root.tag}>"
        for child in root:
            if child.tag != 'testcase':
                LOG.warning(f"Expected <testcase> but received <{child.tag}>")
                continue
            tc_res = self.get_result_fields(child)
            for field in ['test_id', 'status_id']:
                if not tc_res[field]:
                    FieldIsMissed(field=field)
            self.raw_results.append(tc_res)

    def get_result_list(self, xml_file):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        if root.tag == 'testsuites':
            for ts in root:
                self.process_testsuite(ts)
        else:
            self.process_testsuite(root)

        results = {'results': [],
                   'results_setup': [],
                   'results_teardown': []}
        filter_res = {'filter_setup': 'results_setup',
                      'filter_teardown': 'results_teardown'}
        for res in self.raw_results:
            filtered = False
            for fltr, r in filter_res.items():
                if fltr in self.tr_result_attrs:
                    fltr_attrs = self.tr_result_attrs[fltr]
                    pattern = fltr_attrs['match']
                    actions = fltr_attrs['actions']
                    if re.match(pattern, res['test_id']):
                        out = perform_actions(res['test_id'], actions)
                        res['test_id'] = out
                        replace_status = fltr_attrs.get('status')
                        if replace_status:
                            res['status_id'] = replace_status
                        results[r].append(res)
                        filtered = True
            if filtered:
                continue
            results['results'].append(res)
        return results

    def get_result_fields(self, xml_tc):
        tc_res = {}
        for key, val in self.tr_result_attrs.items():
            if key in ['filter_setup', 'filter_teardown']:
                continue
            tc_res[key] = self.perform_xml_actions(xml_tc, val['xml_actions'])
            if not tc_res[key]:
                tc_res[key] = val.get('default')
        return tc_res

    @staticmethod
    def action_get_attribute(child, attr_name):
        for key, value in child.attrib.items():
            if key == attr_name:
                return value

    @staticmethod
    def action_get_element_text(child):
        return child.text

    def perform_xml_actions(self, child, actions, res=''):
        for action in actions:
            if 'add_string' in action:
                res += action['add_string']
            elif 'get_attribute' in action:
                attr_name = action['get_attribute']
                res += self.action_get_attribute(child, attr_name)
            elif 'get_element_text' in action:
                res += self.action_get_element_text(child)
            elif 'has_child_tag' in action:
                for subchild in child:
                    if subchild.tag == action['has_child_tag']:
                        if 'xml_actions' not in action:
                            raise ActionIsMissed(action='xml_actions')
                        res += self.perform_xml_actions(
                            subchild, action['xml_actions'], res=res)
            else:
                raise UnknownAction(action=action)
        return res
