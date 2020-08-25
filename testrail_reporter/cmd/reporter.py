import argparse
import logging
import json

from testrail_reporter.lib.config import Config
from testrail_reporter.lib.settings import TRR_LOG_FILE, TRR_LOG_LEVEL
from testrail_reporter.lib.reportparser import ReportParser
from testrail_reporter.lib.testcaseparser import TestCaseParser
from testrail_reporter.lib.testrailanalyzer import CheckListParser, \
    TestRailAnalyzer
from testrail_reporter.lib.testrailproject import TestRailProject
from testrail_reporter.lib.testrailreporter import TestRailReporter

logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    filename=TRR_LOG_FILE,
    level=TRR_LOG_LEVEL,
)
LOG = logging.getLogger(__name__)


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

    check_list_obj = CheckListParser(args.check_list_path)
    project = TestRailProject(url=config.url,
                              user=config.user,
                              password=config.password,
                              project_name=args.tr_project)
    analyzer = TestRailAnalyzer(project, args.tr_run, args.tr_plan)
    analyzer.analyze_results(check_list_obj)


def publish(args, config):
    LOG.info('========== Publish test results ==========')
    LOG.info('Report file: "{0}"'.format(args.report_path))
    log_settings(args, config)
    LOG.debug('Testrail Test Plan: "{0}"'.format(args.tr_plan))
    LOG.debug('Testrail Test Run: "{0}"'.format(args.tr_run))
    LOG.debug('Suite name: "{0}"'.format(args.tr_suite))
    LOG.debug('Milestone: "{0}"'.format(args.tr_milestone))
    if args.tr_conf is not None:
        tr_conf = json.loads(args.tr_conf.replace("\'", '"'))
    else:
        tr_conf = None

    report = ReportParser(tr_result_attrs=args.tr_result_attrs,
                          tr_result_map=args.tr_result_map)
    results = report.get_result_list(args.report_path)

    reporter = TestRailReporter(url=config.url,
                                user=config.user,
                                password=config.password,
                                project_name=args.tr_project)
    reporter.publish_results(results, args.tr_plan, args.tr_suite, args.tr_run,
                             milestone=args.tr_milestone,
                             configuration=tr_conf,
                             update_existing=True,
                             remove_untested=args.remove_untested)


def update_suite(args, config):
    LOG.info('========== Update Test Suite ==========')
    LOG.info('List of tests: "{0}"'.format(args.tc_list_path))
    log_settings(args, config)
    LOG.debug('Suite name: "{0}"'.format(args.tr_suite))

    tc_parser = TestCaseParser(case_map=args.testcase_map)
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
        '--remove-untested', dest='remove_untested', action="store_true",
        default=False,
        help='Remove untested cases from Test Run'
    )
    parser_b.add_argument(
        '--result-attrs', dest='tr_result_attrs',
        default='testrail_reporter/etc/tr_result_attrs.yaml',
        help='Custom result attributes'
    )
    parser_b.add_argument(
        '--result-map', dest='tr_result_map',
        default='testrail_reporter/etc/maps/tempest/result_template.yaml',
        help='Custom result map'
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
        '--tc-map', dest='testcase_map',
        default='testrail_reporter/etc/maps/tempest/case_template.yaml',
        help='TestCase map'
    )
    parser_c.set_defaults(func=update_suite)
    # =========================================================================
    try:
        args = parser.parse_args()
        args.func(args, config)
    except AttributeError:
        parser.print_help()


if __name__ == "__main__":
    main()
