import yaml


class ReportParser(object):
    def __init__(self, tr_case_attrs='etc/tr_case_attrs.yaml',
                 tr_result_attrs='etc/tr_result_attrs.yaml'):
        with open(tr_case_attrs, 'r') as stream:
            self.tr_case_attrs = yaml.load(stream)
        with open(tr_result_attrs, 'r') as stream:
            self.tr_result_attrs = yaml.load(stream)
        self.suite_list = []
        self.result_list = []
        self.result_list_setUpClass = []


class CheckListParser(object):
    def __init__(self, check_list_attrs='etc/check_list_example.yaml'):
        with open(check_list_attrs, 'r') as stream:
            self.attrs = yaml.load(stream)
        self._check_structure()

    def _check_structure(self):
        for test in self.attrs['tests']:
            if not 'title' in test:
                raise Exception("title not found")
            if not 'status' in test:
                raise Exception("status not found")
            if not 'errors' in test:
                test['errors'] = None
            if not 'defects' in test:
                test['defects'] = None
