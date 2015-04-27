import ConfigParser
from jira import JIRA
from launchpadlib.launchpad import Launchpad

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

def get_jira_bug_verification_tasks(jira_instance, project, release):
    issues_count=1000000,
    issues_fields='key,summary,description,issuetype,priority', 'status,updated,comment,fixVersions'
    filter ='project={0} and issuetype=Task and summary ~ "Bug verification" ' \
            'and labels in (QA, bugs)'.format(project, release)
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
        list_of_bugs = p.searchTasks(assignee=p, status='Fix Committed', milestone=milestone)
        for bug in list_of_bugs:
            bugs.append(bug)
    return bugs

jira = JIRA(basic_auth=(user, password), options={'server': server})

Jtasks = get_jira_bug_verification_tasks(jira, jira_project, release)
lp_bugs = get_launchpad_bugs()
for Lbug in lp_bugs:
    it_created = False
    for Jtask in Jtasks:
        if str(Lbug.bug.id) in Jtask.fields.summary:
            it_created = True
            break

    if not it_created:
        sum = 'Bug verification #'+str(Lbug.bug.id)
        newJtask= jira.create_issue(project=jira_project, summary=sum, description=Lbug.web_link,
                                    labels=['QA', 'bugs'], issuetype={'name': 'Task'})
        print newJtask
        print "Task '{0}' successfully added to Jira".format(newJtask.fields.summary, Lbug.bug.id)
    if it_created:
        print "Bug {0} has task '{1}' in Jira: ".format(Lbug.bug.id, Jtask.fields.summary)

