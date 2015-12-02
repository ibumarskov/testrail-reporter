import sys
#sys.path.append(sys.path[0]+"/fuel-qa")
#sys.path.append('/home/ibumarskov/fuel-qa/fuelweb_test/testrail')

from optparse import OptionParser
import rst
import os
import logging
from testrail import *

LOGS_DIR = os.environ.get('LOGS_DIR', os.getcwd())
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    filename=os.path.join(LOGS_DIR, 'log/generate_test_plan.log'),
                    filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(console)

url = os.environ.get('TESTRAIL_URL')
user = os.environ.get('TESTRAIL_USER')
password = os.environ.get('TESTRAIL_PASSWORD')

def main():
    parser = OptionParser(
        description="Generate Test Plan from TestRail in RST."
                    "See settings.py for configuration."
    )
    parser.add_option('-p', '--project_name', dest='project_name', default=None,
                      help='Name of Test Suite in TestRail')
    parser.add_option('-s', '--suite_name', dest='suite_name', default=None,
                      help='Name of Test Suite in TestRail')
    parser.add_option('-e', '--exclude', dest='sections', default=None,
                      help='Exclude section(s) from Test Suite. Use comma as \
                      delimeter')

    (options, args) = parser.parse_args()

    # STEP #1
    # Initialize TestRail Project and define configuration
    logger.info('Initializing TestRail Project configuration...')
    project_name = options.project_name
    project = TestRailProject(url=url,
                              user=user,
                              password=password,
                              project=project_name)
    logger.info('Initializing TestRail Project configuration... done')

    suite_name = options.suite_name
    exclude_sections = options.sections

    test_suite = project.get_suite_by_name(suite_name)
    all_sections = project.get_sections(test_suite['id'])

    exclude_sections_id = []
    if exclude_sections is not None:
        section_list = exclude_sections.split(',')
        for s in section_list:
            section = project.get_section_by_name(test_suite['id'], s)
            exclude_sections_id.append(section['id'])

    for s in all_sections:
        section_cases = project.get_cases(suite_id=test_suite['id'],
                                          section_id=s['id'])
        section_id = s['id']
        if section_id in exclude_sections_id:
            continue
        doc = rst.Document(s['name'].encode('utf-8'))


        for t in section_cases:
            sec = rst.Section(t['title'].encode('utf-8'),depth=2)
            doc.add_child(sec)

            sec = rst.Section('ID',depth=4)
            doc.add_child(sec)

            para = rst.Paragraph(encode_adv(t['custom_test_group']))
            doc.add_child(para)

            sec = rst.Section('Description',depth=4)
            doc.add_child(sec)

            para = rst.Paragraph(encode_adv(t['custom_test_case_description']))
            doc.add_child(para)

            sec = rst.Section('Complexity',depth=4)
            doc.add_child(sec)
            if t['custom_case_complexity']==1:
                para = rst.Paragraph('smoke')
            elif t['custom_case_complexity']==2:
                para = rst.Paragraph('core')
            elif t['custom_case_complexity']==3:
                para = rst.Paragraph('advanced')
            else:
                para = rst.Paragraph('unknown')
            doc.add_child(para)

            step_depth=4
            sec = rst.Section('Steps', depth=step_depth)
            doc.add_child(sec)

            blt = rst.Orderedlist()
            i=0
            for step in t['custom_test_case_steps']:
                i=i+1
                st = step['content'].encode('utf-8')
                st = st.replace('\n', '\n'+' '*(step_depth+2+len(str(i))))
                blt.add_item(st)
            doc.add_child(blt)


            sec = rst.Section('Expected result', depth=step_depth)
            doc.add_child(sec)

            res = rst.Paragraph(t['custom_test_case_steps'][-1]['expected'].encode('utf-8'))
            doc.add_child(res)

        doc.save("test_suite_" + s['name'].encode('utf-8').lower() + '.rst')

def encode_adv(text):
    try:
        return text.encode('utf-8')
    except:
        return "-"

if __name__ == "__main__":
    main()
