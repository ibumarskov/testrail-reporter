import os
import logging
from jira import JIRA
from launchpadlib.launchpad import Launchpad

logging.basicConfig(filename='log/sync_jira.log', format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)

server = os.getenv('JIRA_URL')
user = os.getenv('JIRA_USER')
password = os.getenv('JIRA_PASSWORD')
jira_project = os.getenv('JIRA_PROJECT')

project = os.getenv('LAUNCHPAD_PROJECT')
team_name = os.getenv('LAUNCHPAD_TEAM')
milestone = os.getenv('LAUNCHPAD_MILESTONE', None)
tags = os.getenv('LAUNCHPAD_TAGS', None)

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
                'Wishlist': 'Some day',
                'Undecided': 'Some day'}

user_map = {'popovych-andrey':'apopovych'}

def get_jira_bugs(jira_instance, project):
    issues_count=1000000,
    issues_fields='key,summary,description,issuetype,priority,labels',\
                  'status,updated,comment,fixVersions'
    filter ='project={0} and issuetype=Bug'.format(project)
    tasks = jira_instance.search_issues(filter, fields=issues_fields,
                                maxResults=issues_count)
    return tasks

def check_duplicate_user(user, peoples):
    for p in peoples:
        if p.name == user.member.name:
            logging.info('User {0} already in list'.format(user.member.name))
            return False
    return True

def return_indirect_members(team, teams=[], peoples=[]):
    for member in team.members_details:
        if member.member.is_team:
            subteam = launchpad.people(member.member.name)
            teams.append(subteam)
            logging.info('{0} - team'.format(subteam))
            return_indirect_members(subteam, teams, peoples)
        else:
            logging.info('{0}'.format(launchpad.people[member.member.name]))
            if check_duplicate_user(member, peoples):
                peoples.append(launchpad.people[member.member.name])
    return teams, peoples

def search_lp_tasks(lp_list):
    bugs = []
    logging.info('Filter: milestone "{0}", tags "{1}"'.format(milestone, tags))
    for user in lp_list:
        list_of_bugs = user.searchTasks(assignee=user, status=lp_jira_map.keys(), milestone=milestone, tags=tags)
        for bug in list_of_bugs:
            bugs.append(bug)
    return bugs

def get_launchpad_bugs():
    cachedir = "~/.launchpadlib/cache/"
    launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)
    team = launchpad.people(team_name)
    bugs = []
    logging.info('Team members:')
    teams, peoples = return_indirect_members(team)
    teams.insert(0, team)
    bugs.extend(search_lp_tasks(teams))
    bugs.extend(search_lp_tasks(peoples))
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
        labels.append(Lbug.status.replace(' ', '_'))
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

logging.info("==============================================")
logging.info("========== SYNC LAUNCHPAD WITH JIRA ==========")
logging.info("==============================================")
jira = JIRA(basic_auth=(user, password), options={'server': server})
Jbugs = get_jira_bugs(jira, jira_project)
lp_bugs = get_launchpad_bugs()

logging.info("{0} Jira bugs were found".format(len(Jbugs)))
logging.info("{0} Launchpad bugs were found".format(len(lp_bugs)))

for Lbug in lp_bugs:
    logging.info("Launchpad bug {0} ({1})".format(Lbug.bug.id, Lbug.title.encode('utf-8')))
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
