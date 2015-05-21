import datetime
import copy
import ConfigParser
from prettytable import PrettyTable
from launchpadlib.launchpad import Launchpad

config = ConfigParser.RawConfigParser()
config.read('sync.cfg')

project = config.get('launchpad', 'project')
team_name = config.get('launchpad', 'team_name')
milestone = config.get('launchpad', 'milestone')
one_week_ago_date = datetime.datetime.now() - datetime.timedelta(weeks=1)

cachedir = "~/.launchpadlib/cache/"
launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir)
lp_team = launchpad.people(team_name).members_details
lp_project = launchpad.projects(project)

table = PrettyTable(["Title", "Importance", "Status", "Assigned To", "Link"])
table.padding_width = 1 # One space between column edges and contents (default)
table.align["Title"] = "l"

print "\n\n\nList of bugs verified during the last week\n"
table_1 = copy.deepcopy(table)
counter = 0
for people in lp_team:
    p = launchpad.people[people.member.name]
    bug_list = p.searchTasks(assignee=p, modified_since=one_week_ago_date, status='Fix Released')
    for bug in bug_list:
        table_1.add_row([bug.title, bug.importance, bug.status, bug.assignee.name, bug.web_link])
        counter += 1
print table_1.get_string(sortby="Importance")
print "Total bugs verified during the last week: {0}".format(counter)


print "\n\n\nList of bugs that need to be fixed:\n"
table_2 = copy.deepcopy(table)
counter = 0
for people in lp_team:
    p = launchpad.people[people.member.name]
    bug_list = p.searchTasks(assignee=p, status=['Incomplete', 'Triaged', 'Confirmed', 'In Progress'],
                             milestone=milestone)
    for bug in bug_list:
        table_2.add_row([bug.title, bug.importance, bug.status, bug.assignee.name, bug.web_link])
        counter += 1
# + bugs assigned to pi-team
pi_team = launchpad.people['fuel-partner']
bug_list = pi_team.searchTasks(assignee=pi_team, status=['Incomplete', 'Triaged', 'Confirmed', 'In Progress'],
                               milestone=milestone)
for bug in bug_list:
    table_2.add_row([bug.title, bug.importance, bug.status, bug.assignee.name, bug.web_link])
    counter += 1
print table_2.get_string(sortby="Status")
print "Total bugs need to be fixed: {0}".format(counter)


print "\n\n\nList of bugs that need to be verified\n"
table_3 = copy.deepcopy(table)
counter=0
for people in lp_team:
    p = launchpad.people[people.member.name]
    bug_list = p.searchTasks(assignee=p, status='Fix Committed', milestone=milestone)
    for bug in bug_list:
        table_3.add_row([bug.title, bug.importance, bug.status, bug.assignee.name, bug.web_link])
        counter += 1
print table_3.get_string(sortby="Importance")
print "Total bugs need to be verified: {0}".format(counter)
