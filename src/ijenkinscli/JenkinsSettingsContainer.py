'''
Created on Jul 23, 2015

@author: nkoester
'''


class JenkinsSettingsContainer():
    host = None
    auth = None
    proxies = None
    ssl_verification = None

    def __init__(self, host, auth, proxies, ssl_verification):
        self.host = host
        self.auth = auth
        self.proxies = proxies
        self.ssl_verification = ssl_verification
