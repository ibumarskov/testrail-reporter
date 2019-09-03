import os


class Config(object):
    def __init__(self):
        self.url = os.environ.get('TESTRAIL_URL')
        self.user = os.environ.get('TESTRAIL_USER')
        self.password = os.environ.get('TESTRAIL_PASSWORD')
