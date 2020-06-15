import copy
import re
import xml.etree.ElementTree as ET
import yaml

from lib.actions import perform_actions


class ReportParser(object):
    def __init__(self,
                 tr_result_attrs='etc/tr_result_attrs.yaml',
                 tr_result_map='etc/maps/tempest/result_template.yaml'):
        with open(tr_result_attrs, 'r') as stream:
            self.tr_result_attrs = yaml.safe_load(stream)
        with open(tr_result_map, 'r') as stream:
            self.tr_result_map = yaml.safe_load(stream)

    def get_result_list(self, xml_file):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        raw_results = []
        for child in root:
            if child.tag != self.tr_result_map['tc_tag']:
                continue
            tc_res = copy.copy(self.tr_result_attrs)

            # Get test name:
            tc_res['test_id'] = self.perform_xml_actions(
                child, self.tr_result_map['test_id']['xml_actions']
            )
            if not tc_res['test_id']:
                Exception("Test_id (title) can'be empty")

            # Get test status:
            tc_res['status_id'] = self.perform_xml_actions(
                child, self.tr_result_map['status_id']['xml_actions']
            )
            if not tc_res['status_id']:
                tc_res['status_id'] = \
                    self.tr_result_map['status_id']['default']

            # Get comments (logs):
            tc_res['comment'] = self.perform_xml_actions(
                child, self.tr_result_map['comment']['xml_actions']
            )
            raw_results.append(tc_res)

        results = {'results': [],
                   'results_setup': [],
                   'results_teardown': []}
        for res in raw_results:
            if 'filter_setup' in self.tr_result_map:
                pattern = self.tr_result_map['filter_setup']['match']
                actions = self.tr_result_map['filter_setup']['actions']
                if re.match(pattern, res['test_id']):
                    out = perform_actions(res['test_id'],
                                          actions)
                    res['test_id'] = out
                    results['results_setup'].append(res)
                    continue

            if 'filter_teardown' in self.tr_result_map:
                pattern = self.tr_result_map['filter_teardown']['match']
                actions = self.tr_result_map['filter_teardown']['actions']
                if re.match(pattern, res['test_id']):
                    out = perform_actions(res['test_id'],
                                          actions)
                    res['test_id'] = out
                    results['results_teardown'].append(res)
                    continue
            results['results'].append(res)
        return results

    @staticmethod
    def action_get_attribute(child, attr_name):
        for key, value in child.attrib.items():
            if key == attr_name:
                return value

    @staticmethod
    def action_get_element_text(child):
        return child.text

    @staticmethod
    def action_check_child(child, attr_name):
        for key, value in child.attrib.items():
            if key == attr_name:
                return value

    @staticmethod
    def check_attribute(child, attr_name):
        if attr_name in child.attrib.keys():
            return True
        else:
            return False

    @staticmethod
    def return_subchild(child, properties):
        for subchild in child:
            tag = False
            attr = False
            if 'tag' in properties:
                if subchild.tag == properties['tag']:
                    tag = True
            else:
                tag = True
            if 'attribute' in properties:
                for attr in subchild.attrib.keys():
                    if attr == properties['attribute']:
                        attr = True
            else:
                attr = True

            if tag and attr:
                return subchild
        return None

    def perform_xml_actions(self, child, actions, res=''):
        for action in actions:
            if 'add_string' in action:
                res += action['add_string']
            elif 'get_attribute' in action:
                attr_name = action['get_attribute']
                res += self.action_get_attribute(child, attr_name)
            elif 'get_element_text' in action:
                res += self.action_get_element_text(child)
            elif 'check' in action:
                if 'parent' in action['check']:
                    nested = action['check']['parent']
                    attr_name = nested['attribute']
                    if self.check_attribute(child, attr_name):
                        res += self.perform_xml_actions(child,
                                                        nested['xml_actions'],
                                                        res=res)
                if 'child' in action['check']:
                    nested = action['check']['child']
                    subchild = self.return_subchild(child, nested)
                    if subchild is not None:
                        res += self.perform_xml_actions(subchild,
                                                        nested['xml_actions'],
                                                        res=res)
            else:
                raise Exception("Unknow action: {}".format(action))
        return res
