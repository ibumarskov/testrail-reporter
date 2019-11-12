import argparse
import logging
import json

from lib.config import Config
from lib.reportparser import CheckListParser
from lib.settings import TRR_LOG_FILE, TRR_LOG_LEVEL
from lib.tempestparser import TempestXMLParser
from lib.testrailanalyzer import TestRailAnalyzer
from lib.testrailproject import TestRailProject
from lib.testrailreporter import TestRailReporter
from lib.reportparser import TestListParser

logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    filename=TRR_LOG_FILE,
    level=TRR_LOG_LEVEL,
)
LOG = logging.getLogger(__name__)


def log_settings(args):
    LOG.debug('URL: "{0}"'.format(config.url))
    LOG.debug('User: "{0}"'.format(config.user))
    LOG.debug('Testrail Project name: "{0}"'.format(args.tr_project))
    LOG.debug('Testrail Test Plan: "{0}"'.format(args.tr_plan))
    LOG.debug('Testrail Test Run: "{0}"'.format(args.tr_run))


def analyze(args):
    LOG.info('========== Run analyzer ==========')
    LOG.info('Check list file: "{0}"'.format(args.check_list_path))
    log_settings(args)

    check_list_obj = CheckListParser(args.check_list_path)
    project = TestRailProject(url=config.url,
                              user=config.user,
                              password=config.password,
                              project_name=args.tr_project)
    analyzer = TestRailAnalyzer(project, args.tr_run, args.tr_plan)
    analyzer.analyze_results(check_list_obj)


def publish(args):
    LOG.info('========== Publish test results ==========')
    LOG.info('Report file: "{0}"'.format(args.report_path))
    log_settings(args)
    LOG.debug('Suite name: "{0}"'.format(args.tr_suite))
    LOG.debug('Milestone: "{0}"'.format(args.tr_milestone))
    if args.tr_conf is not None:
        tr_conf = json.loads(args.tr_conf.replace("\'", '"'))
    else:
        tr_conf = None
    report_obj = TempestXMLParser(args.report_path,
                                  tr_case_attrs=args.tr_case_attrs,
                                  tr_result_attrs=args.tr_result_attrs,
                                  tr_case_map=args.tr_case_map,
                                  tr_result_map=args.tr_result_map,
                                  sections_map=args.sections_map)
    project = TestRailProject(url=config.url,
                              user=config.user,
                              password=config.password,
                              project_name=args.tr_project)
    reporter_obj = TestRailReporter(project, report_obj)
    if args.update_ts:
        reporter_obj.update_test_suite(args.tr_suite)

    reporter_obj.report_test_plan(args.tr_plan, args.tr_suite, args.tr_run,
                                  milestone=args.tr_milestone,
                                  configuration=tr_conf,
                                  update_existing=True,
                                  remove_untested=args.remove_untested)


def update_suite(args):
    LOG.info('========== Update Test Suite ==========')
    LOG.info('List of tests: "{0}"'.format(args.tc_list_path))
    # log_settings(args)
    LOG.debug('Suite name: "{0}"'.format(args.tr_suite))

    # project = TestRailProject(url=config.url,
    #                           user=config.user,
    #                           password=config.password,
    #                           project_name=args.tr_project)
    report_suite_obj = TestListParser(args.tc_list_path)
    pass


def main():
    parser = argparse.ArgumentParser(prog='reporter.py')
    subparsers = parser.add_subparsers(help='additional help')
    # ================================ analyze ================================
    parser_a = subparsers.add_parser(
        'analyze', help='analyze test run failures.')
    parser_a.add_argument(
        'check_list_path', metavar='Check list', type=str,
        help='Path to check list (.yml)'
    )
    parser_a.add_argument(
        '-p', dest='tr_project', default=None,
        help='TestRail Project name.'
    )
    parser_a.add_argument(
        '-t', dest='tr_plan',
        help='TestRail Plan name'
    )
    parser_a.add_argument(
        '-r', dest='tr_run', default=None,
        help='TestRail Run name.'
    )
    parser_a.set_defaults(func=analyze)
    # ================================ publish ================================
    parser_b = subparsers.add_parser(
        'publish', help='publish test results to TestRail.')
    parser_b.add_argument(
        'report_path', metavar='Tempest report', type=str,
        help='Path to tempest report (.xml)'
    )
    parser_b.add_argument(
        '-p', dest='tr_project', default=None,
        help='TestRail Project name.'
    )
    parser_b.add_argument(
        '-t', dest='tr_plan',
        help='TestRail Plan name'
    )
    parser_b.add_argument(
        '-r', dest='tr_run', default=None,
        help='TestRail Run name.'
    )
    parser_b.add_argument(
        '-s', dest='tr_suite', default=None,
        help='TestRail Suite name.'
    )
    parser_b.add_argument(
        '-m', dest='tr_milestone', default=None,
        help='TestRail milestone.'
    )
    parser_b.add_argument(
        '-c', dest='tr_conf', default=None,
        help="Set configuration for test entry (Test Run). "
             "Example: -c \"{'Contrail':'OC 4.1'}\""
    )
    parser_b.add_argument(
        '--update-suite', dest='update_ts', action="store_true",
        default=False,
        help='Update Test Suite'
    )
    parser_b.add_argument(
        '--remove-untested', dest='remove_untested', action="store_true",
        default=False,
        help='Remove untested cases from Test Run'
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
    parser_b.set_defaults(func=publish)
    # ================================ update ================================
    parser_c = subparsers.add_parser(
        'update', help='Update Test Suite in TestRail.')
    parser_c.add_argument(
        'tc_list_path', metavar='List of test cases', type=str,
        help='Path to file with list of tests.'
    )
    parser_c.add_argument(
        '-p', dest='tr_project', default=None,
        help='TestRail Project name.'
    )
    parser_c.add_argument(
        '-s', dest='tr_suite', default=None,
        help='TestRail Suite name.'
    )
    parser_c.set_defaults(func=update_suite)
    # =========================================================================
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    config = Config()
    main()
