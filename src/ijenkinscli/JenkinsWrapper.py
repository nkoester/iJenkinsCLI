'''
Created on Jul 23, 2015

@author: nkoester
'''

import autojenkins


class JenkinsWrapper(object):

    '''
    classdocs
    '''
    settings = None
    jenkins = None

    COLOR_MAPPING = {
        'blue': 'SUCCESS',
        'green': 'SUCCESS',
        'red': 'FAILED',
        'yellow': 'UNSTABLE',
        'aborted': 'ABORTED',
        'disabled': 'DISABLED',
        'grey': 'NOTBUILT',
        'notbuilt': 'NOTBUILT',
        'building': 'BUILDIONG',
    }

    def __init__(self, settings):
        '''
        Constructor
        '''
        self.settings = settings
        self.update_jenkins(self.settings)

    def update_jenkins(self, settings):
        self.settings = settings
        self.jenkins = autojenkins.Jenkins(self.settings.host,
                                           proxies=self.settings.proxies,
                                           auth=self.settings.auth,
                                           verify_ssl_cert=self.settings.ssl_verification)

    def get_detailed_joblist(self):
        return {a_job: self.jenkins.job_info(a_job) for (a_job, _) in self.jenkins.all_jobs()}

    def get_jobs_details(self, job_name):
        return self.jenkins.job_info(job_name)

    def get_last_build_log(self, job_name):
        return self.jenkins.last_build_console(job_name)

    def jenkins_build(self, job_name):
        return self.jenkins.build(job_name)

    def get_job_details(self, job_name):
        pass
