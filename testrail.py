#
# TestRail API binding for Python 2.x (API v2, available since 
# TestRail 3.0)
#
# Learn more:
#
# http://docs.gurock.com/testrail-api2/start
# http://docs.gurock.com/testrail-api2/accessing
#
# Copyright Gurock Software GmbH. See license.md for details.
#

import base64
import json
import urllib2


class APIClient:
    def __init__(self, base_url):
        self.user = ''
        self.password = ''
        if not base_url.endswith('/'):
            base_url += '/'
        self.__url = base_url + 'index.php?/api/v2/'

    #
    # Send Get
    #
    # Issues a GET request (read) against the API and returns the result
    # (as Python dict).
    #
    # Arguments:
    #
    # uri                 The API method to call including parameters
    #                     (e.g. get_case/1)
    #
    def send_get(self, uri):
        return self.__send_request('GET', uri, None)

    #
    # Send POST
    #
    # Issues a POST request (write) against the API and returns the result
    # (as Python dict).
    #
    # Arguments:
    #
    # uri                 The API method to call including parameters
    #                     (e.g. add_case/1)
    # data                The data to submit as part of the request (as
    #                     Python dict, strings must be UTF-8 encoded)
    #
    def send_post(self, uri, data):
        return self.__send_request('POST', uri, data)

    def __send_request(self, method, uri, data):
        url = self.__url + uri
        request = urllib2.Request(url)
        if method == 'POST':
            request.add_data(json.dumps(data))
        auth = base64.b64encode('%s:%s' % (self.user, self.password))
        request.add_header('Authorization', 'Basic %s' % auth)
        request.add_header('Content-Type', 'application/json')

        e = None
        try:
            response = urllib2.urlopen(request).read()
        except urllib2.HTTPError as e:
            response = e.read()

        if response:
            result = json.loads(response)
        else:
            result = {}

        if e != None:
            if result and 'error' in result:
                error = '"' + result['error'] + '"'
            else:
                error = 'No additional error message received'
            raise APIError('TestRail API returned HTTP %s (%s)' %
                           (e.code, error))

        return result


class APIError(Exception):
    pass


class TestRailProject():
    def __init__(self, url, user, password, project):
        self.client = APIClient(base_url=url)
        self.client.user = user
        self.client.password = password
        self.project = self._get_project(project)

    def _get_project(self, project_name):
        projects_uri = 'get_projects'
        projects = self.client.send_get(uri=projects_uri)
        for project in projects:
            if project['name'] == project_name:
                return project
        return None

    def get_suites(self):
        suites_uri = 'get_suites/{project_id}'.format(
            project_id=self.project['id'])
        return self.client.send_get(uri=suites_uri)

    def get_suite(self, suite_id):
        suite_uri = 'get_suite/{suite_id}'.format(suite_id=suite_id)
        return self.client.send_get(uri=suite_uri)

    def get_suite_by_name(self, name):
        for suite in self.get_suites():
            if suite['name'] == name:
                return self.get_suite(suite_id=suite['id'])

    def get_sections(self, suite_id):
        sections_uri = 'get_sections/{project_id}&suite_id={suite_id}'.format(
            project_id=self.project['id'],
            suite_id=suite_id
        )
        return self.client.send_get(sections_uri)

    def get_section(self, section_id):
        section_uri = 'get_section/{section_id}'.format(section_id=section_id)
        return self.client.send_get(section_uri)

    def get_section_by_name(self, suite_id, section_name):
        for section in self.get_sections(suite_id=suite_id):
            if section['name'] == section_name:
                return self.get_section(section_id=section['id'])

    def get_cases(self, suite_id, section_id=None):
        cases_uri = 'get_cases/{project_id}&suite_id={suite_id}'.format(
            project_id=self.project['id'],
            suite_id=suite_id
        )
        if section_id:
            cases_uri = '{0}&section_id={section_id}'.format(
                cases_uri, section_id=section_id
            )
        return self.client.send_get(cases_uri)
