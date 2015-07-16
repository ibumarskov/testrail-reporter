import os
import logging
from jira import JIRA
from launchpadlib.launchpad import Launchpad

logging.basicConfig(filename='log/sync_jira.log', format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)

server = os.getenv('JIRA_URL')
user = os.getenv('JIRA_USER')
password = os.getenv('JIRA_PASSWORD')
jira_project = os.getenv('JIRA_PROJECT')
release = os.getenv('JIRA_RELEASE')
project = os.getenv('LAUNCHPAD_PROJECT')
team_name = os.getenv('LAUNCHPAD_TEAM')
additional_team = os.getenv('LAUNCHPAD_TEAM_2', None)
milestone = os.getenv('LAUNCHPAD_MILESTONE')

cachedir = "~/.launchpadlib/cache/"
launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)
team = launchpad.people(team_name).members_details

lp_jira_map = {'Triaged': 'Open',
               'Confirmed': 'Open',
               'In Progress': 'In Progress',
               'Fix Committed': ['Review', 'Bug Verification', 'Blocked'],
               'Fix Released': 'Done',
               'Invalid': 'Done',
               "Won't Fix": 'Done'}

transition_map = {'Open': 'Stop Progress',
                  'In Progress': 'Start Progress',
                  'Review': 'Review',
                  'Bug Verification': 'Verification',
                  'Blocked': 'Block',
                  'Done': 'Done'}

priority_map = {'Critical': 'Critical',
                'High': 'Major',
                'Medium': 'Nice to have',
                'Low': 'Some day',
                'Wishlist': 'Some day'}

user_map = {'popovych-andrey':'apopovych'}

def get_jira_bugs(jira_instance, project, release):
    issues_count=1000000,
    issues_fields='key,summary,description,issuetype,priority,labels',\
                  'status,updated,comment,fixVersions'
    filter ='project={0} and issuetype=Bug'.format(project, release)
    tasks = jira_instance.search_issues(filter, fields=issues_fields,
                                maxResults=issues_count)
    return tasks

def get_launchpad_bugs():
    cachedir = "~/.launchpadlib/cache/"
    launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)
    team = launchpad.people(team_name).members_details
    bugs = []
    logging.info('Team members:')
    for people in team:
        logging.info('{0}'.format(people))
        p = launchpad.people[people.member.name]
        list_of_bugs = p.searchTasks(assignee=p, status=lp_jira_map.keys(), milestone=milestone)
        for bug in list_of_bugs:
            bugs.append(bug)
    # + bugs assigned to whole team
    if additional_team is not None:
        team2 = launchpad.people[additional_team]
        logging.info('Additional team: {0}'.format(team2))
        team2_bugs = team2.searchTasks(assignee=team2, status=lp_jira_map.keys(), milestone=milestone)
        for bug in team2_bugs:
            bugs.append(bug)
    return bugs

def sync_jira_status(issue, Lbug):
    logging.info('=== Start to sync {0} with launchpad ==='.format(issue.key))
    lp_status = Lbug.status
    set_priority(issue, Lbug)
    update_labels(issue, Lbug)
    if lp_jira_map[lp_status] in ['Open', 'In Progress']:
        assign_bug(issue, Lbug)
    if str(issue.fields.status) in lp_jira_map[lp_status]:
        logging.info('{0} in actual state.'.format(issue.key))
        logging.info('Jira status: {0}, Launchpad status: {1}'.format(issue.fields.status, lp_status))
        return True
    else:
        if lp_status == 'Fix Committed':
            new_status = 'Review'
        else:
            new_status = lp_jira_map[lp_status]
        change_issue_status(issue, new_status)
        logging.info('Status was successfully updated')

def assign_bug(issue, Lbug):
    # Assign bug to developer
    person_link = Lbug.bug.bug_tasks.entries[0]['assignee_link']
    lp_user = person_link.replace('https://api.launchpad.net/1.0/~', '')
    try:
        user = user_map[lp_user]
    except:
        user = lp_user
    try:
        jira.assign_issue(issue, user)
        logging.warning("Issue was assigned to {0}".format(user))
    except:
        logging.error("Can't assign issue to {0}".format(user))

def set_priority(issue, Lbug):
    prio = priority_map[Lbug.importance]
    issue.update(fields={"priority": {'name': prio}})
    logging.info('Importance was change to {0}'.format(prio))

def update_labels(issue, Lbug):
    labels = []
    if len(Lbug.bug.tags) != 0:
        labels = labels + Lbug.bug.tags
    if Lbug.status in ['Invalid', "Won't Fix"]:
        labels.append(Lbug.status)
    if len(labels):
        logging.info('Add following labels: {0}'.format(labels))
        for label in labels:
            issue.fields.labels.append(label)
        issue.update(fields={"labels": issue.fields.labels})

def change_issue_status(issue, new_status):
    logging.info('Changing status from "{0}" to "{1}"'.format(issue.fields.status, new_status))
    is_review = False
    if str(issue.fields.status) == 'Open' and new_status != 'In Progress':
        issue = transition(issue, transition_map['In Progress'])
    if str(issue.fields.status) == 'In Progress' and new_status != 'Review':
        is_review = True
        issue = transition(issue, transition_map['Review'])
    if str(issue.fields.status) == 'Review' and new_status != 'Bug Verification':
        issue = transition(issue, transition_map['Bug Verification'])
    if str(issue.fields.status) in ['Bug Verification', 'Blocked'] and new_status != 'Done':
        issue = transition(issue, transition_map['Open'])
    issue = transition(issue, transition_map[new_status])

    if is_review is True or new_status == 'Review':
        # If bug was moved to Review state necessary to reassign bug from developer to qa
        jira.assign_issue(issue, None)
        logging.warning("Issue was unassigned from {0}".format(issue.fields.assignee))

def transition(issue, transit_status):
    transitions = jira.transitions(issue)
    is_success=False
    for t in transitions:
        if t['name']==transit_status:
            logging.info('status was changed "{0}" -> "{1}"'.format(issue.fields.status, transit_status))
            jira.transition_issue(issue, t['id'])
            is_success=True
            break
    if is_success == False:
        logging.error("Can't change status '{0}' -> '{1}'".format(issue.fields.status, transit_status))
    return jira.issue(issue.id)

jira = JIRA(basic_auth=(user, password), options={'server': server})
Jbugs = get_jira_bugs(jira, jira_project, release)
lp_bugs = get_launchpad_bugs()

logging.info("==============================================")
logging.info("========== SYNC LAUNCHPAD WITH JIRA ==========")
logging.info("==============================================")
logging.info("{0} Jira bugs were found".format(len(Jbugs)))
logging.info("{0} Launchpad bugs were found".format(len(lp_bugs)))

for Lbug in lp_bugs:
    logging.info("Launchpad bug {0} ({1})".format(Lbug.bug.id, Lbug.title))
    it_created = False
    for Jbug in Jbugs:
        if str(Lbug.bug.id) in Jbug.fields.summary:
            logging.info("Matched to Jira issue {0} ({1})".format(Jbug.key, Jbug.fields.summary.encode('utf-8')))
            it_created = True
            sync_jira_status(Jbug, Lbug)
            break
    if not it_created and Lbug.status not in ["Won't Fix", 'Invalid', 'Fix Released']:
        summary = Lbug.title
        newJbug = jira.create_issue(project=jira_project, summary=summary, description=Lbug.web_link,
                                    labels=['launchpad'], issuetype={'name': 'Bug'})
        logging.info("Jira issue {0} ({1}) was successfully added".format(newJbug.key, newJbug.fields.summary.encode('utf-8')))
        issue_dict = {"fixVersions": [{"name": "team"}]}
        newJbug.update(fields=issue_dict)
        sync_jira_status(newJbug, Lbug)
