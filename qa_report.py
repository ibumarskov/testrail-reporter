import argparse
import logging

from lib.config import Config
from lib.reportparser import CheckListParser
from lib.settings import QAR_LOG_FILE, QAR_LOG_LEVEL
from lib.tempestparser import TempestXMLParser
from lib.testrailanalyzer import TestRailAnalyzer
from lib.testrailproject import TestRailProject
from lib.testrailreporter import TestRailReporter


logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    filename=QAR_LOG_FILE,
    level=QAR_LOG_LEVEL,
)
LOG = logging.getLogger(__name__)


def log_settings(args):
    LOG.debug('URL: "{0}"'.format(config.url))
    LOG.debug('User: "{0}"'.format(config.user))
    LOG.debug('Testrail Project name: "{0}"'.format(args.project_name))
    LOG.debug('Testrail Test Plan: "{0}"'.format(args.test_plan_name))
    LOG.debug('Testrail Test Run: "{0}"'.format(args.test_run))


def analyze(args):
    LOG.info('========== Run analyzer ==========')
    LOG.info('Check list file: "{0}"'.format(args.check_list_path))
    log_settings(args)

    check_list_obj = CheckListParser(args.check_list_path)
    project = TestRailProject(url=config.url,
                              user=config.user,
                              password=config.password,
                              project_name=args.project_name)
    analyzer = TestRailAnalyzer(project, args.test_run, args.test_plan_name)
    analyzer.analyze_results(check_list_obj)


def upload(args):
    LOG.info('========== Upload test results ==========')
    LOG.info('Tempest report file: "{0}"'.format(args.report_path))
    log_settings(args)
    LOG.debug('Testrail suite name: "{0}"'.format(args.suite_name))
    LOG.debug('Milestone: "{0}"'.format(args.milestone))

    report_obj = TempestXMLParser(args.report_path,
                                  tr_case_attrs=args.tr_case_attrs,
                                  tr_result_attrs=args.tr_result_attrs,
                                  tr_case_map=args.tr_case_map,
                                  tr_result_map=args.tr_result_map,
                                  sections_map=args.sections_map)
    project = TestRailProject(url=config.url,
                              user=config.user,
                              password=config.password,
                              project_name=args.project_name)
    reporter_obj = TestRailReporter(project, report_obj)
    if args.update_ts:
        reporter_obj.update_test_suite(args.suite_name)
    reporter_obj.report_test_plan(args.test_plan_name, args.suite_name,
                                  args.test_run, update_existing=True,
                                  remove_untested=args.remove_untested)


def main():
    parser = argparse.ArgumentParser(prog='qa_report')
    subparsers = parser.add_subparsers(help='additional help')

    parser_a = subparsers.add_parser(
        'analyze', help='analyze test report failures.')
    parser_a.add_argument(
        'check_list_path', metavar='Check list', type=str,
        help='Path to check list (.yml)'
    )
    parser_a.add_argument(
        '-p', dest='project_name', default=None,
        help='Testrail project name.'
    )
    parser_a.add_argument(
        '-t', dest='test_plan_name',
        help='Testrail Test Plan name'
    )
    parser_a.add_argument(
        '-r', dest='test_run', default=None,
        help='Testrail Test Run name.'
    )
    parser_a.set_defaults(func=analyze)

    parser_b = subparsers.add_parser(
        'upload', help='upload test results to TestRail.')
    parser_b.add_argument(
        'report_path', metavar='Tempest report', type=str,
        help='Path to tempest report (.xml)'
    )
    parser_b.add_argument(
        '-p', dest='project_name', default=None,
        help='Testrail project name.'
    )
    parser_b.add_argument(
        '-t', dest='test_plan_name',
        help='Testrail Test Plan name'
    )
    parser_b.add_argument(
        '-r', dest='test_run', default=None,
        help='Testrail Test Run name.'
    )
    parser_b.add_argument(
        '-s', dest='suite_name', default=None,
        help='Testrail suite name.'
    )
    parser_b.add_argument(
        '-m', dest='milestone', default=None,
        help='Testrail milestone.'
    )
    parser_b.add_argument(
        '-u', dest='update_ts', action="store_true", default=False,
        help='Update Test Suite'
    )
    parser_b.add_argument(
        '-c', dest='remove_untested', action="store_true", default=False,
        help='Update Test Suite'
    )
    parser_b.add_argument(
        '--case-attrs', dest='tr_case_attrs',
        default='etc/tr_case_attrs.yaml',
        help='Custom case attributes'
    )
    parser_b.add_argument(
        '--result-attrs', dest='tr_result_attrs',
        default='etc/tr_result_attrs.yaml',
        help='Custom result attributes'
    )
    parser_b.add_argument(
        '--case-map', dest='tr_case_map',
        default='etc/maps/tempest/tr_case.yaml',
        help='Custom case map'
    )
    parser_b.add_argument(
        '--result-map', dest='tr_result_map',
        default='etc/maps/tempest/tr_result.yaml',
        help='Custom result map'
    )
    parser_b.add_argument(
        '--sections-map', dest='sections_map',
        default='etc/maps/tempest/sections.yaml',
        help='Custom section map'
    )
    parser_b.set_defaults(func=upload)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    config = Config()
    main()
