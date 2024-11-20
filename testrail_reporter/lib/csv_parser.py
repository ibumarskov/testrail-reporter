import csv

from testrail_reporter.lib.reportparser import ReportParser


class CSVParser(ReportParser):

    def _process_map(self, row, map):
        default = None
        val = None
        if 'default' in map:
            default = map['default']
        if 'row_name' in map:
            val = row[map['row_name']]
        if not val and default:
            val = default
        if 'convert_type' in map:
            val = self.convert(val, map['convert_type'])
        return val

    def get_result_list(self):
        results = {'results': [],
                   'results_setup': [],
                   'results_teardown': []}
        with open(self.file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tc_res = {key: None for key in self.tr_result_map.keys()}
                for key_trm, map_trm in self.tr_result_map.items():
                    tc_res[key_trm] = self._process_map(row, map_trm)
                # Drop aggregated results
                if tc_res['test_id'] == "Aggregated":
                    continue
                self.raw_results.append(tc_res)
        results['results'] = self.raw_results
        return results
