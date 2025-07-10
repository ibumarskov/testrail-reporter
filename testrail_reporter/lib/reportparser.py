import yaml


class ReportParser(object):

    def __init__(self, file, tr_result_attrs, tr_result_map):
        self.file = file
        with open(tr_result_attrs, 'r') as stream:
            self.tr_result_attrs = yaml.safe_load(stream)
        with open(tr_result_map, 'r') as stream:
            self.tr_result_map = yaml.safe_load(stream)
        self._raw_results = []

    @staticmethod
    def convert(value, ctype):
        if ctype == "int":
            return int(value.split('.')[0])
        elif ctype == "str":
            return str(value)
        elif ctype == "bool":
            return bool(value)
        elif ctype == "":
            return value
        else:
            raise Exception(f"Unknown type for conversion: {ctype}")

    @property
    def raw_results(self):
        if not self._raw_results:
            self.processing()
        return self._raw_results

    def processing(self):
        pass

    def get_result_list(self):
        pass
