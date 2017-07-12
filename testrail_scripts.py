import datetime
import logging
import os
import time

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
project_name = os.environ.get('TESTRAIL_PROJECT')
milestone = os.environ.get('TESTRAIL_MILESTONE')

project = TestRailProject(url=url,
                          user=user,
                          password=password,
                          project_name=project_name)


def close_outdated_runs(created_before_days=30, milestone_name=None):
    ago = datetime.datetime.now() - datetime.timedelta(created_before_days)
    timestamp = int(time.mktime(ago.timetuple()))
    filter = '&is_completed=0&created_before={}'.format(timestamp)
    if milestone_name is not None:
        milestone = project.get_milestone_by_name(milestone_name)
        filter += '&milestone_id={}'.format(milestone['id'])
    runs = project.get_runs_project(filter)
    plans = project.get_plans_project(filter)

    for i, run in enumerate(runs):
        project.close_plan(run['id'])
        logger.info("{i}. Run '{run}' was closed.".format(i=i,
                                                          run=run['name']))

    for i, plan in enumerate(plans):
        project.close_run(plan['id'])
        logger.info("{i}. Plan '{plan}' was closed.".format(i=i,
                                                            plan=plan['name']))

if __name__ == "__main__":
    close_outdated_runs(milestone_name=milestone)
