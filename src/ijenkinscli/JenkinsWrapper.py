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
    OPTION_LABEL_JOB_INFO = "Job Info"
    OPTION_LABEL_BUILD = "Build"
    OPTION_LABEL_LAST_BUILD_LOG = "Last Build Log"

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

    def get_available_jobs(self):
        retval = {"name": "Available Jobs", "children": []}
        joblist = self.jenkins.all_jobs()

        for i, (job_name, color) in enumerate(joblist):
            if '_anime' in color:
                color = color.split('_')[0]
                color = 'building'

            retval['children'].append({"name": (self.COLOR_MAPPING[color], job_name)})
            retval['children'][i]['children'] = []
            retval['children'][i]['children'].append({"name": self.OPTION_LABEL_JOB_INFO})
            retval['children'][i]['children'].append({"name": self.OPTION_LABEL_BUILD})
            retval['children'][i]['children'].append({"name": self.OPTION_LABEL_LAST_BUILD_LOG})

        return retval, joblist

    def get_jobs_details(self, job_name):
        return self.jenkins.last_build_console(job_name)

    def get_last_build_log(self, job_name):
        return self.jenkins.last_build_console(job_name)

    def jenkins_build(self, job_name):
        return self.jenkins.build(job_name)

    def get_job_details(self, job_name):
        pass
