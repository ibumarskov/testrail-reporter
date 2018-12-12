import yaml


class ReportParser(object):
    def __init__(self, tr_case_attrs='etc/tr_case_attrs.yaml',
                 tr_result_attrs='etc/tr_result_attrs.yaml'):
        with open(tr_case_attrs, 'r') as stream:
            self.tr_case_attrs = yaml.load(stream)
        with open(tr_result_attrs, 'r') as stream:
            self.tr_result_attrs = yaml.load(stream)
