import os
import copy
import datetime
import re
from prettytable import PrettyTable
from launchpadlib.launchpad import Launchpad

project = os.getenv('LAUNCHPAD_PROJECT')
team_name = os.getenv('LAUNCHPAD_TEAM')
milestone = os.getenv('LAUNCHPAD_MILESTONE', None)
tags = os.getenv('LAUNCHPAD_TAGS', None)
one_week_ago_date = datetime.datetime.now() - datetime.timedelta(weeks=1)

cachedir = "~/.launchpadlib/cache/"
lp_api = 'devel'
launchpad = Launchpad.login_anonymously('just testing', 'production', cachedir,
                                        version=lp_api)
lp_team = launchpad.people(team_name).members_details
lp_project = launchpad.projects(project)

table = PrettyTable(["Title", "Milestone", "Importance", "Status", "Assigned To", "Link"])
table.padding_width = 1 # One space between column edges and contents (default)
table.align["Title"] = "l"

def trim_milestone(milestone):
    return re.sub('https:.*/', '', str(milestone))

def check_duplicate_user(user, peoples):
    for p in peoples:
        if p.name == user.member.name:
            return False
    return True

def return_indirect_members(team, teams=[], peoples=[]):
    for member in team.members_details:
        if member.member.is_team:
            subteam = launchpad.people(member.member.name)
            teams.append(subteam)
            return_indirect_members(subteam, teams, peoples)
        else:
            if check_duplicate_user(member, peoples):
                peoples.append(launchpad.people[member.member.name])
    return teams, peoples

def get_lp_bugs(teams, peoples, **kwargs):
    table_lp = copy.deepcopy(table)
    counter = 0
    for people in peoples:
        bug_list = people.searchTasks(assignee=people, **kwargs)
        for bug in bug_list:
            table_lp.add_row([bug.title, trim_milestone(bug.milestone), bug.importance, bug.status, bug.assignee.name, bug.web_link])
            counter += 1
    # + bugs assigned to whole team
    for team in teams:
        bug_list = team.searchTasks(assignee=team, **kwargs)
        for bug in bug_list:
            table_lp.add_row([bug.title, trim_milestone(bug.milestone), bug.importance, bug.status, bug.assignee.name, bug.web_link])
            counter += 1
    return table_lp, counter

team = launchpad.people(team_name)
teams, peoples = return_indirect_members(team)
teams.insert(0, team)

print "\n\n\nList of bugs found during the last week\n"
tbl, counter = get_lp_bugs(teams, peoples, created_since=one_week_ago_date, milestone=milestone, tags=tags)
print tbl.get_string(sortby="Importance")
print "Total bugs found during the last week: {0}".format(counter)

print "\n\n\nList of bugs verified during the last week\n"
tbl, counter = get_lp_bugs(teams, peoples, modified_since=one_week_ago_date, status='Fix Released', milestone=milestone, tags=tags)
print tbl.get_string(sortby="Importance")
print "Total bugs verified during the last week: {0}".format(counter)

print "\n\n\nList of bugs that need to be fixed:\n"
tbl, counter = get_lp_bugs(teams, peoples, status=['New', 'Incomplete', 'Triaged', 'Confirmed', 'In Progress'], milestone=milestone, tags=tags)
print tbl.get_string(sortby="Status")
print "Total bugs need to be fixed: {0}".format(counter)

print "\n\n\nList of bugs that need to be verified\n"
tbl, counter = get_lp_bugs(teams, peoples, status='Fix Committed', milestone=milestone, tags=tags)
print tbl.get_string(sortby="Importance")
print "Total bugs need to be verified: {0}".format(counter)
