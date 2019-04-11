import argparse
import logging
import os

from lib.testrailproject import TestRailProject
from lib.reportparser import CheckListParser
from lib.testrailanalyzer import TestRailAnalyzer

LOGS_DIR = os.environ.get('LOGS_DIR', os.getcwd())
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    filename=os.path.join(LOGS_DIR, 'log/analyze_results.log'),
)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Upload tests cases to '
                                                 'TestRail.')
    parser.add_argument('check_list_path', metavar='Check list', type=str,
                        help='Path to check list (.yml)')
    parser.add_argument('-p', dest='project_name', default=None,
                        help='Testrail project name.')
    parser.add_argument('-t', dest='test_plan_name',
                        help='Testrail Test Plan name')
    parser.add_argument('-r', dest='test_run', default=None,
                        help='Testrail Test Run name.')
    return parser.parse_args()


def main():
    args = parse_arguments()

    url = os.environ.get('TESTRAIL_URL')
    user = os.environ.get('TESTRAIL_USER')
    password = os.environ.get('TESTRAIL_PASSWORD')

    LOG.info('URL: "{0}"'.format(url))
    LOG.info('User: "{0}"'.format(user))
    LOG.info('Check list file: "{0}"'.format(args.check_list_path))
    LOG.info('Testrail project name: "{0}"'.format(args.project_name))
    LOG.info('Testrail Test Plan: "{0}"'.format(args.test_plan_name))
    LOG.info('Testrail Test Run: "{0}"'.format(args.test_run))

    check_list_obj = CheckListParser(args.check_list_path)
    project = TestRailProject(url=url,
                              user=user,
                              password=password,
                              project_name=args.project_name)
    analyzer = TestRailAnalyzer(project, args.test_run, args.test_plan_name)
    analyzer.analyze_results(check_list_obj)


if __name__ == "__main__":
    main()
