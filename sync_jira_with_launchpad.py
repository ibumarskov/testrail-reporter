import os
import logging
import itertools
import json
from jira import JIRA
from launchpadlib.launchpad import Launchpad

LOGS_DIR = os.environ.get('LOGS_DIR', os.getcwd())
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    filename=os.path.join(LOGS_DIR, 'log/sync_jira.log'),
                    filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(console)

jira_url = os.getenv('JIRA_URL')
jira_user = os.getenv('JIRA_USER')
jira_pwd = os.getenv('JIRA_PASSWORD')
jira_project = os.getenv('JIRA_PROJECT')

lp_team = os.getenv('LAUNCHPAD_TEAM')
milestones = json.loads(os.getenv('LAUNCHPAD_MILESTONE', [None]))
lp_project = os.getenv('LAUNCHPAD_PROJECT')
tags = os.getenv('LAUNCHPAD_TAGS', None)

cachedir = "~/.launchpadlib/cache/"
lp_api = 'devel'
launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir, version=lp_api)

lp_jira_map = {'New': 'To Do',
               'Triaged': 'To Do',
               'Confirmed': 'In Progress',
               'In Progress': 'In Progress',
               'Fix Committed': 'In QA',
               'Fix Released': 'Done',
               'Invalid': 'Done',
               "Won't Fix": 'Done'}

transition_map = {'To Do': 'Stop Progress',
                  'In Progress': 'Start Bugfixing',
                  'In QA': 'Start Verification',
                  'Done': 'Done'}

priority_map = {'Critical': 'Critical',
                'High': 'Major',
                'Medium': 'Nice to have',
                'Low': 'Some day',
                'Wishlist': 'Some day',
                'Undecided': 'Some day'}

user_map = {'popovych-andrey': 'apopovych',
            'slavchick': 'vtabolin'}


def get_jira_bugs(jira_instance, project):
    issues_count = 1000000,
    issues_fields = 'key,summary,description,issuetype,priority,labels',\
                  'status,updated,comment,fixVersions'
    query = 'project={0} and issuetype=Bug and ' \
            'resolution=Unresolved'.format(project)
    tasks = jira_instance.search_issues(query, fields=issues_fields,
                                        maxResults=issues_count)
    return tasks


def check_duplicate_user(user, peoples):
    for p in peoples:
        if p.name == user.member.name:
            logger.info('User {0} already in list'.format(user.member.name))
            return False
    return True


def return_indirect_members(team, teams=[], peoples=[]):
    for member in team.members_details:
        if member.member.is_team:
            subteam = launchpad.people(member.member.name)
            teams.append(subteam)
            logger.info('{0} - team'.format(subteam))
            return_indirect_members(subteam, teams, peoples)
        else:
            logger.info('{0}'.format(launchpad.people[member.member.name]))
            if check_duplicate_user(member, peoples):
                peoples.append(launchpad.people[member.member.name])
    return teams, peoples


def search_lp_tasks(lp_users):
    bugs = []
    logger.info('Search bugs using filter with milestones "{0}"'.format(
        milestones.keys(), tags))
    for user, m in itertools.product(lp_users, milestones.keys()):
        milestone = launchpad.projects[lp_project].getMilestone(name=m)
        list_of_bugs = milestone.searchTasks(assignee=user,
                                             status=lp_jira_map.keys(),
                                             tags=tags, omit_duplicates=False)
        for bug in list_of_bugs:
            bugs.append(bug)
    return bugs


def get_launchpad_bugs():
    team = launchpad.people(lp_team)
    bugs = []
    logger.info('Team members:')
    teams, peoples = return_indirect_members(team)
    teams.insert(0, team)
    bugs.extend(search_lp_tasks(teams))
    bugs.extend(search_lp_tasks(peoples))
    return bugs


def sync_jira_status(issue, Lbug):
    logger.info('=== Start to sync {0} with launchpad ==='.format(issue.key))
    if Lbug.bug.duplicate_of:
        lp_status = "Won't Fix"
    else:
        lp_status = Lbug.status
    set_priority(issue, Lbug)
    update_labels(issue, Lbug)
    if lp_jira_map[lp_status] in ['To Do', 'In Progress']:
        assign_bug(issue, Lbug)
    if str(issue.fields.status) in lp_jira_map[lp_status]:
        logger.info('{0} in actual state.'.format(issue.key))
        logger.info('Jira status: {0}, Launchpad status: {1}'.format(
            issue.fields.status, lp_status))
        return True
    else:
        new_status = lp_jira_map[lp_status]
        change_issue_status(issue, new_status)
        logger.info('Status was successfully updated')


def assign_bug(issue, Lbug):
    # Assign bug to developer
    person_link = Lbug.bug.bug_tasks.entries[0]['assignee_link']
    lp_user = person_link.replace('https://api.launchpad.net/'+lp_api+'/~', '')
    try:
        user = user_map[lp_user]
    except:
        user = lp_user
    try:
        jira.assign_issue(issue, user)
        logger.warning("Issue was assigned to {0}".format(user))
    except:
        jira.assign_issue(issue, None)
        logger.error("Can't assign issue to {0}".format(user))


def set_priority(issue, Lbug):
    prio = priority_map[Lbug.importance]
    issue.update(fields={"priority": {'name': prio}})
    logger.info('Importance was change to {0}'.format(prio))


def update_labels(issue, Lbug):
    labels = []
    if len(Lbug.bug.tags) != 0:
        labels = labels + Lbug.bug.tags
    if Lbug.status in ['Invalid', "Won't Fix"]:
        labels.append(Lbug.status.replace(' ', '_'))
    if len(labels):
        logger.info('Add following labels: {0}'.format(labels))
        for label in labels:
            issue.fields.labels.append(label)
        issue.update(fields={"labels": issue.fields.labels})


def change_issue_status(issue, new_status):
    logger.info('Changing status from "{0}" to "{1}"'.format(
        issue.fields.status, new_status))
    if str(issue.fields.status) == 'To Do' and new_status != 'In Progress':
        issue = transition(issue, transition_map['In Progress'])
    if str(issue.fields.status) == 'In Progress' and new_status != 'In QA':
        issue = transition(issue, transition_map['In QA'])
    issue = transition(issue, transition_map[new_status])
    if new_status == 'In QA':
        # If bug was moved to Fix Committed state necessary to
        # reassign bug from developer to qa
        jira.assign_issue(issue, None)
        logger.warning("Issue was unassigned from {0}".format(
            issue.fields.assignee))


def transition(issue, transit_status):
    transitions = jira.transitions(issue)
    is_success = False
    for t in transitions:
        if t['name']==transit_status:
            logger.info('status was changed "{0}" -> "{1}"'.format(
                issue.fields.status, transit_status))
            jira.transition_issue(issue, t['id'])
            is_success = True
            break
    if not is_success:
        logger.error("Can't change status '{0}' -> '{1}'".format(
            issue.fields.status, transit_status))
    return jira.issue(issue.id)

logger.info("==============================================")
logger.info("========== SYNC LAUNCHPAD WITH JIRA ==========")
logger.info("==============================================")
jira = JIRA(basic_auth=(jira_user, jira_pwd), options={'server': jira_url})
Jbugs = get_jira_bugs(jira, jira_project)
lp_bugs = get_launchpad_bugs()

logger.info("{0} Jira bugs were found".format(len(Jbugs)))
logger.info("{0} Launchpad bugs were found".format(len(lp_bugs)))

for Lbug in lp_bugs:
    m = str(Lbug.milestone).replace('https://api.launchpad.net/'+ lp_api + '/'
                                    + lp_project + '/+milestone/', '')
    logger.info("{0} milestone: {1}".format(Lbug.title.encode('utf-8'), m))
    it_created = False
    for Jbug in Jbugs:
        if str(Lbug.bug.id) in Jbug.fields.summary:
            for ver in Jbug.fields.fixVersions:
                if milestones[m] in ver.name:
                    logger.info("Matched to Jira issue {0} ({1})".format(
                        Jbug.key, Jbug.fields.summary.encode('utf-8')))
                    it_created = True
                    sync_jira_status(Jbug, Lbug)
                    break
    if not it_created and not Lbug.bug.duplicate_of and Lbug.status not in \
            ["Won't Fix", 'Invalid', 'Fix Released']:
        summary = Lbug.title
        newJbug = jira.create_issue(project=jira_project,
                                    summary=summary,
                                    description=Lbug.web_link,
                                    labels=['launchpad'],
                                    issuetype={'name': 'Bug'})
        logger.info("Jira issue {0} ({1}) was successfully added".format(
            newJbug.key, newJbug.fields.summary.encode('utf-8')))
        issue_dict = {"fixVersions": [{"name": milestones[m]}]}
        newJbug.update(fields=issue_dict)
        sync_jira_status(newJbug, Lbug)
