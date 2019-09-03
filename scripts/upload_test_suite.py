import logging
import os
import re
from optparse import OptionParser

from docutils.core import publish_doctree

from lib.testrail import APIError
from lib.testrailproject import TestRailProject

LOGS_DIR = os.environ.get('LOGS_DIR', os.getcwd())
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    filename=os.path.join(LOGS_DIR, 'log/upload_test_plan.log')
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(console)

url = os.environ.get('TESTRAIL_URL')
user = os.environ.get('TESTRAIL_USER')
password = os.environ.get('TESTRAIL_PASSWORD')

complexity_map = {
    'smoke': 1,
    'core': 2,
    'advanced': 3
}


def parse_rst(testplan):
    with open(testplan) as f:
        rst_file = []
        for i in f.read():
            rst_file.append(i)
    rst = ''.join(rst_file).replace('`', '\`').replace('*', '\*')
    doctree = publish_doctree(rst)

    suite = []

    section_num = -1
    test_num = -1
    map_attr_to_prop = {
        u'id': 'ID',
        u'description': 'Description',
        u'complexity': 'Complexity'
    }

    for doc_node in doctree.children:

        if doc_node.tagname == 'title':  # =====
            section_num += 1
            suite.append({})

            suite[section_num]['Section'] = doc_node[0].astext()
            suite[section_num]['Tests'] = []
            test_num = -1

        elif doc_node.tagname == 'section':  # -----
            test_num += 1
            suite[section_num]['Tests'].append({})
            test = suite[section_num]['Tests'][test_num]

            test['Title'] = doc_node[0].astext()
            steps = []
            last_expected_res = ''

            for test_node in doc_node.children:
                test_property = test_node.children[-1].astext()
                attr = test_node.attributes['dupnames']

                if attr and attr[0] in map_attr_to_prop:
                    test[map_attr_to_prop[attr[0]]] = test_property
                elif attr == [u'expected result']:
                    last_expected_res = test_property
                elif attr == [u'steps']:
                    test['custom_test_case_steps'] = []
                    steps = filter(lambda x: x.tagname == 'block_quote',
                                   test_node.children)[0][0]

            test['custom_test_case_steps'] = [{
                'content': '\n'.join(map(lambda x: x.astext(), step)),
                'expected': ''
            } for step in steps]

            test['custom_test_case_steps'][-1][u'expected'] = last_expected_res

    return suite


def print_section_header(section):
    logger.info("=========================================")
    logger.info("================ SECTION ================")
    logger.info("=========================================")
    logger.info(section)


def parse_arguments():
    parser = OptionParser(
        description="Upload tests cases to TestRail. "
                    "See settings.py for configuration."
    )
    parser.add_option('-t', dest='path', default=None,
                      help='Path to testplan. Mandatory argument !')
    parser.add_option('-r', dest='pattern', default='test_suite.*\.rst',
                      help='Regex for testplan files.')
    parser.add_option('-p', dest='project_name', default=None,
                      help='Testrail project name. Mandatory argument !')
    parser.add_option('-s', dest='suite_name', default=None,
                      help='Testrail suite name. Mandatory argument !')
    parser.add_option('-m', dest='milestone', default=None,
                      help='Milestone.')
    parser.add_option('-d', action="store_true", dest='dry', default=False,
                      help='Dry run mode. Only show what would be changed and'
                           ' do nothing.')

    (options, _) = parser.parse_args()

    return options


def main():
    options = parse_arguments()

    logger.info('URL: "{0}"'.format(url))
    logger.info('User: "{0}"'.format(user))
    logger.info('Test plan path: "{0}"'.format(options.path))
    logger.info('Testrail project name: "{0}"'.format(options.project_name))
    logger.info('Testrail suite name: "{0}"'.format(options.suite_name))
    logger.info('Milestone: "{0}"'.format(options.milestone))
    if options.dry:
        logger.info('Dry run mode is active')

    pattern = re.compile(options.pattern)
    rst_sections = []

    for f in os.listdir(options.path):
        if pattern.match(f):
            rst_sections += parse_rst(os.path.join(options.path, f))

    project = TestRailProject(url=url,
                              user=user,
                              password=password,
                              project_name=options.project_name)

    suite_id = project.get_suite_by_name(options.suite_name)['id']

    testrail_sections = project.get_sections(suite_id)
    rst_sections_names = [s['Section'] for s in rst_sections]

    case_fields = project.get_case_fields(suite_id)
    qa_teams = filter(lambda x: x['system_name'] == 'custom_qa_team',
                      case_fields)[0]['configs'][0]['options']['items']
    pce_team_id = filter(lambda x: 'PCE' in x,
                         qa_teams.split('\n'))[0].split(', ')[0]

    milestones = project.get_milestones()
    milestone = filter(lambda x: encode_to_utf(x['name']) == options.milestone,
                       milestones)
    milestone = milestone[0]['id'] if milestone else 0

    # Delete existing sections, which are not in rst
    for section in testrail_sections:
        section_name = encode_to_utf(section['name'])

        if section_name not in rst_sections_names:
            print_section_header(section_name)
            logger.warning("Section {0} will be deleted".format(section_name))

            if not options.dry:
                logger.error("NOT DRY RUN !")
                try:
                    project.delete_section(section['id'])
                except APIError, e:
                    logger.error(e)

    for rst_section in rst_sections:
        section_name = rst_section['Section']
        print_section_header(section_name)

        testrail_section = None
        for s in testrail_sections:
            if s['name'] == section_name:
                testrail_section = s

        if not testrail_section:
            logger.warning("Section {0} will be created".format(section_name))

            if not options.dry:
                logger.warning("NOT DRY RUN !")
                project.add_section_project(dict(suite_id, section_name))
                testrail_section = project.get_section_by_name(suite_id,
                                                               section_name)
            else:
                continue

        testrail_tests = project.get_cases(suite_id, testrail_section['id'])
        rst_tests_titles = [x['Title'] for x in rst_section['Tests']]

        # Delete existing tests which are not in rst
        for test in testrail_tests:
            title = test['title']

            if title not in rst_tests_titles:
                logger.info("============== TEST ==============")
                logger.info(title)

                logger.warning("Test '{0}' will be deleted".format(title))
                if not options.dry:
                    logger.warning("NOT DRY RUN !")
                    try:
                        project.delete_case(test['id'])
                    except APIError, e:
                        logger.error(e)

                testrail_tests.remove(test)

        for rst_test in rst_section['Tests']:
            test_title = rst_test['Title']
            logger.info("============== TEST ==============")
            logger.info(test_title)

            test_case_to_upload = {
                "title": test_title,
                "milestone_id": milestone,
                "custom_qa_team": pce_team_id
            }

            test = filter(lambda x: x['title'] == test_title, testrail_tests)
            rst_group = rst_test['ID']
            rst_descr = rst_test['Description']
            rst_complex = complexity_map[rst_test['Complexity'].lower()]
            rst_steps = rst_test['custom_test_case_steps']

            if not test:
                logger.warning("Test will be created")

                logger.debug('Complexity: {0}, Group: '
                             '{1}'.format(rst_complex, rst_group))

                test_case_to_upload.update({
                    "custom_case_complexity": rst_complex,
                    "custom_test_group": rst_group,
                    "custom_test_case_description": rst_descr,
                    "custom_test_case_steps": rst_steps
                })

                for i, step in enumerate(rst_steps):
                    logger.debug('Will be created step {0} with '
                                 'description\n{1}'
                                 ''.format(i, encode_to_utf(step['content'])))
                    if step['expected']:
                        logger.debug('Expected:\n{0}'.format(step['expected']))

                if not options.dry:
                    logger.warning("NOT DRY RUN !")
                    project.add_case(testrail_section['id'],
                                     test_case_to_upload)
            else:
                updated = False

                # Test group (ID)
                cur_group = test[0]['custom_test_group']
                if cur_group != rst_group:
                    updated = True
                    logger.warning(
                        "Test Group will be changed from '{0}' to "
                        "'{1}'".format(cur_group, rst_group))
                    test_case_to_upload['custom_test_group'] = rst_group

                # Test description
                cur_descr = test[0]['custom_test_case_description']
                if cur_descr != rst_descr:
                    updated = True
                    logger.warning(
                        "Test Description will be changed from '{0}' to "
                        "'{1}'".format(cur_descr, rst_descr))
                    test_case_to_upload['custom_test_case_description'] = \
                        rst_descr

                # Test complexity
                cur_complex = test[0]['custom_case_complexity']
                if cur_complex != rst_complex:
                    updated = True
                    logger.warning(
                        "Test Complexity will be changed from '{0}' to "
                        "'{1}'".format(cur_complex, rst_complex))
                    test_case_to_upload['custom_case_complexity'] = rst_complex

                # Test steps
                cur_steps = test[0]['custom_test_case_steps']
                warning_printed = -1

                i = 0
                for i, step in enumerate(rst_steps):
                    is_new = False
                    try:
                        cur_step = cur_steps[i]
                    except IndexError:
                        logger.warning('Step {0} will be created'.format(i+1))
                        warning_printed = 0
                        is_new = True

                    if is_new or cur_step['content'] != step['content']:
                        updated = True
                        warning_printed += 1
                        if not warning_printed:
                            logger.warning("Steps description will be changed")

                        logger.warning('Description for step {0} will be '
                                       'changed'.format(i+1))
                        logger.debug(
                            "\nOld description: \n{0}\nNew description: \n"
                            "{1}".format(step['content'], cur_step['content'])
                        )
                    if is_new or cur_step['expected'] != step['expected']:
                        updated = True
                        warning_printed += 1
                        if not warning_printed:
                            logger.warning("Steps description will be changed")

                        logger.warning('Expected result for step {0} will be '
                                       'changed'.format(i+1))
                        logger.debug(
                            "\nOld expected: \n{0}\nNew expected: \n{1}"
                            "".format(step['expected'], cur_step['expected'])
                        )

                steps_amount = len(cur_steps) - 1
                for r in xrange(i, steps_amount):
                    logger.warning('Step {0} will be removed'
                                   ''.format(r+1))

                if warning_printed != -1:
                    test_case_to_upload["custom_test_case_steps"] = rst_steps

                if not options.dry and updated:
                    logger.warning("NOT DRY RUN !")
                    project.update_case(test[0]['id'], test_case_to_upload)
                else:
                    logger.info('Was not updated')


def encode_to_utf(text):
    try:
        return text.encode('utf-8')
    except UnicodeEncodeError:
        return "-"

if __name__ == "__main__":
    main()
