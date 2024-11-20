import argparse
import json
import logging
import sys

import pkg_resources

from testrail_reporter.lib.config import Config
from testrail_reporter.lib.dynamic_parser import DynamicReportParser
from testrail_reporter.lib.settings import TRR_LOG_FILE, TRR_LOG_LEVEL
from testrail_reporter.lib.testcaseparser import TestCaseParser
from testrail_reporter.lib.testrailanalyzer import (CheckListParser,
                                                    TestRailAnalyzer)
from testrail_reporter.lib.testrailproject import TestRailProject
from testrail_reporter.lib.testrailreporter import TestRailReporter

logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    filename=TRR_LOG_FILE,
    level=TRR_LOG_LEVEL,
)
LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler(sys.stdout))


def log_settings(args, config):
    LOG.debug('URL: "{0}"'.format(config.url))
    LOG.debug('User: "{0}"'.format(config.user))
    LOG.debug('Testrail Project name: "{0}"'.format(args.tr_project))


def analyze(args, config):
    LOG.info('========== Run analyzer ==========')
    LOG.info('Check list file: "{0}"'.format(args.check_list_path))
    log_settings(args, config)
    LOG.debug('Testrail Test Plan: "{0}"'.format(args.tr_plan))
    LOG.debug('Testrail Test Run: "{0}"'.format(args.tr_run))
    LOG.debug('Testrail configuration: "{0}"'.format(args.tr_conf))

    if args.tr_conf is not None:
        tr_conf = json.loads(args.tr_conf.replace("\'", '"'))
    else:
        tr_conf = None

    check_list_obj = CheckListParser(args.check_list_path)
    project = TestRailProject(url=config.url,
                              user=config.user,
                              password=config.password,
                              project_name=args.tr_project)
    analyzer = TestRailAnalyzer(project, args.tr_run, plan_name=args.tr_plan,
                                configuration=tr_conf)
    analyzer.analyze_results(check_list_obj)


def publish(args, config):
    LOG.info('========== Publish test results ==========')
    LOG.info('Report file: "{0}"'.format(args.report_path))
    log_settings(args, config)
    LOG.debug('Testrail Test Plan: "{0}"'.format(args.tr_plan))
    LOG.debug('Testrail Test Run: "{0}"'.format(args.tr_run))
    LOG.debug('Testrail configuration: "{0}'.format(args.tr_conf))
    LOG.debug('Suite name: "{0}"'.format(args.tr_suite))
    LOG.debug('Milestone: "{0}"'.format(args.tr_milestone))

    if not args.tr_result_attrs:
        rpath = '/'.join(('etc', 'tr_result_attrs.yaml'))
        tr_result_attrs = pkg_resources.resource_filename("testrail_reporter",
                                                          rpath)
    else:
        tr_result_attrs = args.tr_result_attrs
    if not args.tr_result_map:
        rpath = '/'.join(('etc/maps', args.map, 'result_template.yaml'))
        tr_result_map = pkg_resources.resource_filename("testrail_reporter",
                                                        rpath)
    else:
        tr_result_map = args.tr_result_attrs
    if args.tr_conf is not None:
        tr_conf = json.loads(args.tr_conf.replace("\'", '"'))
    else:
        tr_conf = None

    parser = DynamicReportParser(args.report_path,
                                 tr_result_attrs=tr_result_attrs,
                                 tr_result_map=tr_result_map)
    results = parser.get_result_list()

    reporter = TestRailReporter(url=config.url,
                                user=config.user,
                                password=config.password,
                                project_name=args.tr_project)
    reporter.publish_results(results, args.tr_plan, args.tr_suite, args.tr_run,
                             milestone=args.tr_milestone,
                             configuration=tr_conf,
                             update_existing=True,
                             remove_untested=args.remove_untested,
                             remove_skipped=args.remove_skipped,
                             comm_limit=args.limit,
                             tr_limit=args.tr_limit,
                             tr_plan_descr=args.tr_plan_descr,
                             tr_run_descr=args.tr_run_descr)


def update_suite(args, config):
    LOG.info('========== Update Test Suite ==========')
    LOG.info('List of tests: "{0}"'.format(args.tc_list_path))
    log_settings(args, config)
    LOG.debug('Suite name: "{0}"'.format(args.tr_suite))

    if not args.tr_case_attrs:
        rpath = '/'.join(('etc', 'tr_case_attrs.yaml'))
        tr_case_attrs = pkg_resources.resource_filename("testrail_reporter",
                                                        rpath)
    else:
        tr_case_attrs = args.tr_case_attrs
    if not args.tr_case_map:
        rpath = '/'.join(('etc/maps', args.map, 'case_template.yaml'))
        tr_case_map = pkg_resources.resource_filename("testrail_reporter",
                                                      rpath)
    else:
        tr_case_map = args.tr_result_attrs

    tc_parser = TestCaseParser(tr_case_attrs=tr_case_attrs,
                               tr_case_map=tr_case_map)
    tc_list = tc_parser.get_tc_list(args.tc_list_path)

    reporter = TestRailReporter(url=config.url,
                                user=config.user,
                                password=config.password,
                                project_name=args.tr_project)
    reporter.update_test_suite(args.tr_suite, tc_list)


def main():
    config = Config()
    parser = argparse.ArgumentParser(prog='testrail-reporter')
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
    parser_a.add_argument(
        '-c', dest='tr_conf', default=None,
        help="Set configuration for test entry (Test Run). "
             "Example: -c \"{'Operating Systems':'Ubuntu 18.04'}\""
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
             "Example: -c \"{'Operating Systems':'Ubuntu 18.04'}\""
    )
    parser_b.add_argument(
        '--plan-description', dest='tr_plan_descr', default=None,
        help="Test Plan description."
    )
    parser_b.add_argument(
        '--run-description', dest='tr_run_descr', default=None,
        help="Test Run description."
    )
    parser_b.add_argument(
        '--limit', dest='limit', default=100000, type=int,
        help='Limit the length of the comments (characters, 0 is unlimited.)'
    )
    parser_b.add_argument(
        '--tr-limit', dest='tr_limit', default=0, type=int,
        help='Limit for results data sended within one POST request '
             '(bytes, 0 is unlimited.).'
    )
    parser_b.add_argument(
        '--remove-untested', dest='remove_untested', action="store_true",
        default=False,
        help='Remove untested cases from Test Run'
    )
    parser_b.add_argument(
        '--remove-skipped', dest='remove_skipped', action="store_true",
        default=False,
        help='Remove skipped cases from Test Run'
    )
    parser_b.add_argument(
        '--result-attrs', dest='tr_result_attrs',
        default=None,
        help='Set path to config file with custom result attributes '
             '(.yaml format).'
    )
    parser_b.add_argument(
        '--map', dest='map',
        default='tempest',
        help='Use predefined map for parsing attributes. Supported values:'
             'tempest, pytest, locust',
    )
    parser_b.add_argument(
        '--result-map', dest='tr_result_map',
        default=None,
        help='Set path to config file with custom result map. '
             'Note: this parameter overrides predefined map parameter.'
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
    parser_c.add_argument(
        '--case-attrs', dest='tr_case_attrs',
        default=None,
        help='Set path to config file with custom case attributes '
             '(.yaml format).'
    )
    parser_c.add_argument(
        '--map', dest='map',
        default='tempest',
        help='Use predefined map for parsing case attributes. Supported '
             'values: tempest, pytest'
    )
    parser_c.add_argument(
        '--tc-map', dest='tr_case_map',
        default=None,
        help='Set path to config file with custom case map. '
             'Note: this parameter overrides predefined map parameter.'
    )
    parser_c.set_defaults(func=update_suite)
    # =========================================================================
    args = parser.parse_args()
    args.func(args, config)


if __name__ == "__main__":
    main()
