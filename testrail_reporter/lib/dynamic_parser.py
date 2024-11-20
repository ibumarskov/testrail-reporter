import os

from testrail_reporter.lib.csv_parser import CSVParser
from testrail_reporter.lib.xml_parser import XMLParser


class DynamicReportParser(object):
    file_name = None
    file_extension = None

    def __new__(self, file, *arg, **kwargs):
        self.file_name, self.file_extension = os.path.splitext(file)
        if self.file_extension == ".csv":
            return CSVParser(file, *arg, **kwargs)
        elif self.file_extension == ".xml":
            return XMLParser(file, *arg, **kwargs)
        else:
            raise ValueError(f"Unsupported file type: "
                             f"{self.file_name}{self.file_extension}")
