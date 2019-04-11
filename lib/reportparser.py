import yaml


class ReportParser(object):
    def __init__(self, tr_case_attrs='etc/tr_case_attrs.yaml',
                 tr_result_attrs='etc/tr_result_attrs.yaml'):
        with open(tr_case_attrs, 'r') as stream:
            self.tr_case_attrs = yaml.load(stream)
        with open(tr_result_attrs, 'r') as stream:
            self.tr_result_attrs = yaml.load(stream)


class CheckListParser(object):
    def __init__(self, check_list_attrs='etc/check_list_example.yaml'):
        with open(check_list_attrs, 'r') as stream:
            self.check_list_attrs = yaml.load(stream)
