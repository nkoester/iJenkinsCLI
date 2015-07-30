'''
Created on Jul 30, 2015

@author: nkoester
'''


import autojenkins


CONSOLE = '{0}/job/{1}/{2}/consoleText'


def _validate(response):
    """
    Verify the status code of the response and raise exception on codes > 400.
    """
    message = 'HTTP Status: {0}'.format(response.status_code)
    if response.status_code >= 400:
        exception_cls = autojenkins.jobs.HTTP_ERROR_MAP.get(response.status_code, autojenkins.jobs.HttpStatusError)
        raise exception_cls(message)
    return response

autojenkins.jobs._validate = _validate


class Jenkins(autojenkins.Jenkins):

    def build_console(self, jobname, build_number=None):
        """
        Get the console output for the build of a job.

        If no build number is specified, defaults to the most recent build.
        """
        if build_number is not None:
            args = (CONSOLE, jobname, build_number)
        else:
            args = (CONSOLE, jobname, "lastBuild")
        response = self._build_get(*args)
        return response.content

    def last_build_console(self, jobname):
        """
        Get the console output for the last build of a job.
        """
        return self.build_console(jobname)
