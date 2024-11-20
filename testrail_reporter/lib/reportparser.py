import yaml


class ReportParser(object):

    def __init__(self, file, tr_result_attrs, tr_result_map):
        self.file = file
        with open(tr_result_attrs, 'r') as stream:
            self.tr_result_attrs = yaml.safe_load(stream)
        with open(tr_result_map, 'r') as stream:
            self.tr_result_map = yaml.safe_load(stream)
        self.raw_results = []

    @staticmethod
    def convert(value, ctype):
        match ctype:
            case "int":
                return int(value.split('.')[0])
            case "str":
                return str(value)
            case "bool":
                return bool(value)
            case "":
                return value
            case _:
                raise Exception(f"Unknown type for conversion: {ctype}")

    def get_result_list(self):
        pass
