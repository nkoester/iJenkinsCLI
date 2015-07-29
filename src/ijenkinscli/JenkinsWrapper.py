'''
Created on Jul 23, 2015

@author: nkoester
'''
import collections
from itertools import izip as zip, count
import pprint

import autojenkins


class JenkinsWrapper(object):

    '''
    classdocs
    '''
    settings = None
    jenkins = None

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

    def get_detailed_joblist(self, status_function):

        status_function("Fetching complete joblist... (this may take a while)")
        jobs = {a_job: self.jenkins.job_info(a_job) for (a_job, _) in self.jenkins.all_jobs()}

        jobs = collections.OrderedDict(sorted(jobs.items(), key=lambda t: t[0]))

        # return {a_job: self.jenkins.job_info(a_job) for (a_job, _) in self.jenkins.all_jobs()}
        # set the 'info' field of each build to None
        for v in jobs.values():
            for b in v['builds']:
                b['info'] = None

        keyword_list = ('lastBuild', 'lastFailedBuild', 'lastCompletedBuild', 'lastStableBuild', 'lastSuccessfulBuild', 'lastUnstableBuild', 'lastUnsuccessfulBuild')

        total_jobs = len(jobs.keys())
        for i, (a_job, a_info) in enumerate(jobs.iteritems()):
            status_function("Processing job {} of {}".format(i + 1, total_jobs))
            #             print "    ...", a_job
            build_ids_to_fetch = []

            # create a list of builds to fetch for the current job. ignores duplicates.
            for keyword in keyword_list:
                # could be None!
                last_X_build_number = a_info[keyword]
                if last_X_build_number:
                    # add if not already there
                    if last_X_build_number['number'] not in build_ids_to_fetch:
                        build_ids_to_fetch.append(last_X_build_number['number'])

            # create a dict of {index:build_id} for the above identified builds
            last_X_index = {a_info['builds'].index(j): j['number'] for j in a_info['builds'] if j['number'] in build_ids_to_fetch}

            # actually query Jenkins for the identified builds and store in the big dict as 'info'
            for a_dict_index, a_build_id in last_X_index.iteritems():
                jobs[a_job]['builds'][a_dict_index]['info'] = self.jenkins.build_info(a_job, build_number=a_build_id)

        status_function("Finished loading of {} jobs!".format(total_jobs))
        return jobs

    def get_jobs_details(self, job_name):
        return self.jenkins.job_info(job_name)

    def get_last_build_log(self, job_name):
        return self.jenkins.last_build_console(job_name)

    def jenkins_build(self, job_name):
        return self.jenkins.build(job_name)

    def get_job_details(self, job_name):
        pass
