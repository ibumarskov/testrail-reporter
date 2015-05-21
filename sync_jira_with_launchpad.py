import ConfigParser
import logging
from jira import JIRA
from launchpadlib.launchpad import Launchpad

logging.basicConfig(filename='log/sync_jira.log', format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
config = ConfigParser.RawConfigParser()
config.read('sync.cfg')

server = config.get('JIRA', 'URL')
user = config.get('JIRA', 'user')
password = config.get('JIRA', 'password')
jira_project = config.get('JIRA', 'project_key')
release = config.get('JIRA', 'release')
project = config.get('launchpad', 'project')
team_name = config.get('launchpad', 'team_name')
milestone = config.get('launchpad', 'milestone')

cachedir = "~/.launchpadlib/cache/"
launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)
team = launchpad.people(team_name).members_details

bug_status = ['Triaged', 'Confirmed', 'In Progress', 'Fix Committed']

def get_jira_bugs(jira_instance, project, release):
    issues_count=1000000,
    issues_fields='key,summary,description,issuetype,priority', 'status,updated,comment,fixVersions'
    filter ='project={0} and issuetype=Bug'.format(project, release)
    tasks = jira_instance.search_issues(filter, fields=issues_fields,
                                maxResults=issues_count)
    return tasks

def get_launchpad_bugs():
    cachedir = "~/.launchpadlib/cache/"
    launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)
    team = launchpad.people(team_name).members_details
    bugs = []
    for people in team:
        p = launchpad.people[people.member.name]
        list_of_bugs = p.searchTasks(assignee=p, status=bug_status, milestone=milestone)
        for bug in list_of_bugs:
            bugs.append(bug)
    # + bugs assigned to pi-team
    pi_team = launchpad.people['fuel-partner']
    pi_team_bugs = pi_team.searchTasks(assignee=pi_team, status=bug_status, milestone=milestone)
    for bug in pi_team_bugs:
        bugs.append(bug)
    return bugs

lp_jira_map = {'Triaged': 'Open',
               'Confirmed': 'Open',
               'In Progress': 'In Progress',
               'Fix Commited': ['Review', 'Bug Verification', 'Blocked'],
               'Fix Released': 'Done'}

transition_map = {'Open': 'Stop Progress',
                  'In Progress': 'Start Progress',
                  'Review': 'Review',
                  'Bug Verification': 'Verification',
                  'Blocked': 'Block',
                  'Done':'Done'}

def sync_jira_status(issue, lp_status):
    logging.info('===== Start to sync Jira Bug "{0}" with Launchpad ====='.format(str(issue.fields.summary)))

    if str(issue.fields.status) in lp_jira_map[str(lp_status)]:
        logging.info('Issue "{0}" in actual state. Jira status: {1}, Launchpad status: {2}'.format(issue.fields.summary,
                                                                                                   issue.fields.status,
                                                                                                   lp_status))
        return True
    else:
        if lp_status == 'Fix Commited':
            new_status = 'Review'
        else:
            new_status = lp_jira_map[lp_status]
        change_issue_status(issue, new_status)
        logging.info('Status was successfully updated')

def change_issue_status(issue, new_status):
    logging.info('= Changing status from "{0}" to "{1}" ='.format(issue.fields.status, new_status))
    is_review = False
    if str(issue.fields.status) == 'Open' and new_status != 'In Progress':
        issue = transition(issue, transition_map['In Progress'])
    if str(issue.fields.status) == 'In progress' and new_status != 'Review':
        is_review = True
        issue = transition(issue, transition_map['Review'])
    if str(issue.fields.status) == 'Review' and new_status != 'Bug Verification':
        issue = transition(issue, transition_map['Bug Verification'])
    if str(issue.fields.status) in ['Bug Verification', 'Blocked'] and new_status != 'Done':
        issue = transition(issue, transition_map['Open'])
    transition(issue, transition_map[new_status])

    if is_review is True or new_status == 'Review':
        # If bug was moved to Review state necessary to reassign bug from developer to qa
        logging.warning("Issue was unassigned from {0}".format(issue.fields.assignee))
        jira.assign_issue(issue, None)

def transition(issue, transit_status):
    transitions = jira.transitions(issue)
    is_success=False
    for t in transitions:
        if t['name']==transit_status:
            logging.info('-> Transition status from "{0}" to "{1}"'.format(issue.fields.status, transit_status))
            jira.transition_issue(issue, t['id'])
            is_success=True
            break
    if is_success == False:
        logging.error("Can't change status '{0}' to '{1}'".format(issue.fields.status, transit_status))
    return jira.issue(issue.id)

jira = JIRA(basic_auth=(user, password), options={'server': server})
Jbugs = get_jira_bugs(jira, jira_project, release)
lp_bugs = get_launchpad_bugs()

logging.info("========== START TO SYNC LAUNCHPAD WITH JIRA ==========")
logging.info("{0} Jira bugs were found".format(len(Jbugs)))
logging.info("{0} Launchpad bugs were found".format(len(lp_bugs)))

for Lbug in lp_bugs:
    it_created = False
    for Jbug in Jbugs:
        if str(Lbug.bug.id) in Jbug.fields.summary:
            logging.info("Bug '{0}' matches to Jira issue '{1}'".format(Lbug.bug.id, Jbug.fields.summary))
            it_created = True
            sync_jira_status(Jbug, Lbug.status)
            break

    if not it_created:
        summary = Lbug.title
        newJbug = jira.create_issue(project=jira_project, summary=summary, description=Lbug.web_link,
                                    labels=['launchpad'], issuetype={'name': 'Bug'})
        logging.info("Issue '{0}' successfully added to Jira".format(newJbug.fields.summary))
        sync_jira_status(newJbug, Lbug.status)
